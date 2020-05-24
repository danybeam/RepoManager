import argparse
import errno
import os
import platform
import sys
import shutil
import yaml

actions = {
    "init": {"dart": 1}
}

licenses = {
    "GPL3": {
        "name": "GNU General Public License version 3",
        "liberties": "Use it comercially, distributing and modifying for both personal and patent use\n  If you use this code you have to:\n  Make the source code available.\n  Copy the copiright and license notice.\n  Document your changes and release them under the same license."
    }
}

parser = argparse.ArgumentParser(
    description='Initialize a project to work with github (does not init git)', prog="projmanager")

parser.add_argument('action', type=str,
                    help='action to be performed  options [init]')
parser.add_argument('language', type=str,
                    help='language of the project (case sensitive) options: [dart]')
parser.add_argument('--in', '--inpath', metavar='<path>', type=str, default=os.path.dirname(os.path.abspath(__file__)),
                    help='the root of the reference project (usually unnecesary)')
parser.add_argument('--out', '--outpath', metavar='<path>', type=str, default=os.getcwd(),
                    help='the root of the destination project (default: current dir)')

args = vars(parser.parse_args())
root = args["in"] or args["inpath"]
cwd = args["out"] or args["outpath"]

if not (actions.get(args["action"], False)).get(args["language"], False):
    print(
        "there is not an action recorded for that language\nIf you would like to see it done please open a ticket in the repo https://github.com/danybeam/RepoManager/issues")
    sys.exit()

# workflows/*

projectName = input(
    "Input project name (defaullt: Unamed-project): ") or "Unamed-project"
goodThings = input(
    "What we are looking for: ") or "code contributions"
notGoodThings = input(
    "what we are not looking for: ") or "No ban in particular :)"
effort = input("What is this for? ") or "this project"
lic = None or "GPL3"  # replace none with parsed arg


def substituteStrings(inpath, outpath, lang):
    infile = open(inpath, "r")
    outfile = open(outpath, "w")
    for line in infile.readlines():
        if "<#" not in line:
            outfile.write(line)
            continue
        line = line.replace("<#LICENSE#>", licenses[lic]["name"])
        line = line.replace("<#LIBERTIES AND RESPONSABILITIES#>",
                            licenses[lic]["liberties"])
        line = line.replace("<#PROJECT NAME#>", projectName)
        line = line.replace("<#MORE THINGS#>", goodThings)
        line = line.replace("<#NOT GOOD THINGS#>", notGoodThings)
        line = line.replace("<#THING#>", effort)
        line = line.replace("<#LANGUAGE#>", lang)
        outfile.write(line)


def dartInit():
    data = None

    # Build CI workflow
    with open(root+r'/hub/workflows/_CI.yml', "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        data["on"] = data.pop(True)
        data["name"] = data["name"].replace(r'<#LANGUAGE#>', "Dart")
        data["jobs"]["test"]["steps"][1]["with"]["paths"] = r'^pubspec.yaml ^README.md'
        data["jobs"]["test"]["steps"][3]["run"] = r'pub get'
        data["jobs"]["test"]["steps"][4]["name"] = r'run tests and generate coverage data and badge'
        data["jobs"]["test"]["steps"][4]["run"] = r'pub run test_coverage'
        data["jobs"]["test"]["steps"].pop(5)
        data["jobs"]["test"]["steps"].pop(5)

    filename = cwd+r'/.github/workflows/dart_CI.yml'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        yaml.dump(data, f)

    # Build test workflow
    with open(root+r'/hub/workflows/_test.yml', "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        data["on"] = data.pop(True)
        data["name"] = data["name"].replace(r'<#LANGUAGE#>', "Dart")
        data["jobs"]["test"]["steps"][1]["run"] = r'pub get'
        data["jobs"]["test"]["steps"][2]["name"] = r'run tests and generate coverage data and badge'
        data["jobs"]["test"]["steps"][2]["run"] = r'pub run test_coverage'

    filename = cwd+r'/.github/workflows/dart_test.yml'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        yaml.dump(data, f)

    # Build release workflow
    with open(root+r'/hub/workflows/_release.yml', "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        data["on"] = data.pop(True)
        data["jobs"]["tag_release"]["steps"][1]["run"] = "dartdoc"
        data["jobs"]["tag_release"]["steps"][3]["with"]["root"] = r'./pubspec.yaml'
        data["jobs"]["tag_release"]["steps"][3]["with"][
            "regex_pattern"] = r'^((0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)$'

    filename = cwd+r'/.github/workflows/dart_release.yml'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        yaml.dump(data, f)

    filename = cwd+r'/Test/test.dart'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        dartTests = [r"import 'package:test/test.dart';",
                     r"import 'package:task_parser/task_parser.dart';",
                     r"void main(){",
                     "  test(\"first test\", () {",
                     r"    expect(true, false);",
                     r"});"]
        f.writelines("%s\n" % l for l in dartTests)

    files = [
        r'/hub/ISSUE_TEMPLATE/bug_report.md',
        r'/hub/ISSUE_TEMPLATE/feature_request.md',
        r'/hub/pull_request_template.md',
        r'/CODE_OF_CONDUCT.md',
        r'/CONTRIBUTING.md',
        r'/Templates/README.md'
    ]
    for f in files:
        out = f.replace(r'/Templates', r'')
        out = out.replace(r'hub', r'.github')
        os.makedirs(os.path.dirname(cwd+out), exist_ok=True)
        substituteStrings(root+f, cwd+out, "Dart")


actions["init"]["dart"] = dartInit
actions[args["action"]][args["language"]]()
