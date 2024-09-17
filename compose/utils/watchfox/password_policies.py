import ast
from collections import defaultdict
import importlib
import json
import os
from pathlib import Path
import re
import sys
import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from typing import Dict, Any, List

os.environ['FLASK_ENV'] = 'development'
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Or any other valid database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'  # Set a secret key for the Flask app
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing purposes

db = SQLAlchemy(app)
app.app_context().push()

CLASS_LOOKUPS = {"FlaskForm", "Form"}
FIELD_LOOKUPS = ["password", "password1", "password2", "passwd", "pwd", "pass"]
METHOD_LOOKUPS = ["DataRequired", "EqualTo", "ValidationError", "Length", "Regexp"]

def detect_password_validators(source_code: ast.Module|str|Path) -> pd.DataFrame:
    
    # Parse the Python file into an AST
    if isinstance(source_code, (str, Path)):
        try: 
            with open(source_code, "r") as file:
                source_code = ast.parse(file.read(), filename=source_code)
        except Exception as e:
            return pd.DataFrame()

    # Store the results in a dictionary
    result = {"class_name": [], "options": []}

    # Function to extract form classes and their password validators
    def extract_validators_from_class(class_node: ast.ClassDef) -> Dict[str, List[Dict[str, Any]]]:
        validators = {}
        for class_body_node in class_node.body:
            if isinstance(class_body_node, ast.FunctionDef):
                match = re.match(rf"validate_({'|'.join(FIELD_LOOKUPS)})", class_body_node.name)
                if match:
                    field_name = match.group(1)
                    if field_name not in validators:
                        validators[field_name] = []
                    # Detect if the method takes a 'field' argument
                    takes_field = any(arg.arg == 'field' for arg in class_body_node.args.args)
                    validators[field_name].append({
                        "name": class_body_node.name,
                        "class_method": True,
                        "takes_field": takes_field,
                        "args": []  # No arguments for class-defined validators
                    })
            elif isinstance(class_body_node, ast.Assign):
                # Check for password fields and their validators
                for target in class_body_node.targets:
                    if isinstance(target, ast.Name) and target.id in FIELD_LOOKUPS:
                        if target.id not in validators:
                            validators[target.id] = []
                        if isinstance(class_body_node.value, ast.Call):
                            for keyword in class_body_node.value.keywords:
                                if keyword.arg == "validators" and isinstance(keyword.value, ast.List):
                                    for elt in keyword.value.elts:
                                        if isinstance(elt, ast.Call) and isinstance(elt.func, ast.Name) and elt.func.id in METHOD_LOOKUPS:
                                            # Extract arguments of the validator function
                                            args = [ast.literal_eval(arg) for arg in elt.args]
                                            kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in elt.keywords}
                                            validators[target.id].append({
                                                "name": elt.func.id,
                                                "class_method": False,
                                                "takes_field": False,
                                                "args": args,
                                                "kwargs": kwargs
                                            })
        return validators

    # Traverse all class definitions in the AST
    for node in ast.walk(source_code):
        if isinstance(node, ast.ClassDef):
            # Check if the class is a form (inherits from a typical Flask form library)
            is_form_class = any(base.id in CLASS_LOOKUPS for base in node.bases if isinstance(base, ast.Name))
            if is_form_class:
                class_name = node.name
                validators = extract_validators_from_class(node)
                for field, valids in validators.items():
                    for validator in valids:
                        result["class_name"].append(class_name)
                        result["options"].append({
                            "field": field,
                            "validator": validator["name"],
                            "class_method": validator["class_method"],
                            "takes_field": validator["takes_field"],
                            "args": validator.get("args", []),
                            "kwargs": validator.get("kwargs", {})
                        })

    return pd.DataFrame(result)

def run_coverage_test(module_path: str, validators: pd.DataFrame, test_passwords: Dict[str, Dict[str, Any]], detailed: bool=False) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_path)
    except Exception as e:
        return {}
    
    if not detailed:
        consolidate_results = defaultdict(lambda: True)
    
    validator_results = {}
    for i, validator in validators.iterrows():

        slug = f"{validator['class_name']}_{validator['options']['validator']}_{i}"
        validator_results[slug] = {}

        if validator['options']['class_method']:
            try:
                klass = getattr(module, validator["class_name"])
                validator_name = validator["options"]["validator"]
                if validator["options"]["takes_field"]:
                    test_validator = lambda password: getattr(klass(), validator_name)(type('', (object,), {'data': password})())
                else:
                    test_validator = lambda password: getattr(klass(), validator_name)(password)
                
                for password, info in test_passwords.items():
                    try:
                        test_validator(password)
                        validator_results[slug][info.get('label')] = info.get('is_valid')
                    except Exception as e:
                        validator_results[slug][info.get('label')] = not info.get('is_valid')
            except (AttributeError, KeyError) as e:
                continue
        else:
            # validators declared in the password field
            if validator['options']['validator'] == "Length":
                # hardcoded `short_pass` label here
                validator_results[slug]['short_pass'] = validator['options']['kwargs'].get('min', 0) >= 8 
            elif validator['options']['validator'] == "Regexp":
                regex = re.compile(validator['options']['args'][0])
                for password, info in test_passwords.items():
                    validator_results[slug][info.get('label')] = (re.search(regex, password) is not None) and info.get('is_valid')
                
        if not detailed:
            for test, status in validator_results[slug].items():
                consolidate_results[test] &= status
        
        if validator_results[slug] == {}: validator_results.pop(slug)
    
    return validator_results if detailed else consolidate_results
 

if __name__ == '__main__':
    import argparse
    from watchfox import CONFIG_PATH
    
    parser = argparse.ArgumentParser(description="WatchFox script with file monitoring and password policy testing.")
    parser.add_argument('-c', '--config', type=str, default=CONFIG_PATH, help="Path to the configuration file.")
    parser.add_argument('-i', '--input', type=str, default='app/forms.py', help="Path to the file to process.")
    parser.add_argument('-m', '--mod_name', type=str, default='app.forms', help="Name of the module to run coverage test on.")
    parser.add_argument('-d', '--detailed', action='store_true', help="Boolean flag for detailed output (optional).")

    args = parser.parse_args()

    with open(args.config, 'r') as config_file:
        config = json.load(config_file)
    
    sys.path.append(config['basedir'])

    # Detect password validators
    validators = detect_password_validators(args.input)
    df_results = run_coverage_test(args.mod_name, validators, config['test_passwords'], args.detailed)
    print(json.dumps(df_results, indent=4))
