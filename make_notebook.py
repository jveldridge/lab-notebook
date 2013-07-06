#!/usr/bin/python
import re
import os, shutil, sys
from ArgParser import *

def parse_args(raw_args):  
    
    description = "Resolves and copies references, converts Markdown to HTML, and checks the\
                   result into the specified git repo. Note that some or all parameters can be\
                   specified via a configuration file by passing '@<ConfigFileName>' as a\
                   command-line parameter, e.g. 'python make_notebook.py @MyConfig.txt'."
    parser = BetterFileArgParser(description=description, fromfile_prefix_chars='@')

    parser.add_argument('-g', '--git_repo_dir', help='Path to the git repo for the lab notebook',
                        required=True)
    parser.add_argument('-c', '--convert_cmd', help='Command to run to convert Markdown to HTML',
                        required=True)
    parser.add_argument('-f', '--file', help='Path to markdown file to convert', required=True)
    parser.add_argument('-m', '--message', help='Git commit message', required=True)

    return parser.parse_args(raw_args)

def load_file(file):
    with open(file) as f:
        return f.read()

def get_references(text):
    return [match for match in re.findall("\[.*?\]\((.*?)\)", text)
                if not match.startswith(('http://', 'https://', '/data/'))]

def copy_and_replace_references(file):
    ref_folder_name = os.path.basename(file)[:os.path.basename(file).find(".md")] + "-resources"
    ref_folder_path = os.path.dirname(os.path.abspath(file)) + '/' + ref_folder_name
    
    if not os.path.exists(ref_folder_path):
        os.mkdir(ref_folder_path)

    text = load_file(file)

    for reference in get_references(text):
        dst = ref_folder_path + "/" + os.path.basename(reference)
        shutil.copytree(reference, dst) if os.path.isdir(reference) else shutil.copyfile(reference, dst)
        text = text.replace(reference, dst)

    return text

def write_to_file(file, text):
    with open(file, 'w') as f:
        f.write(text)
    f.close()

def add_to_index_if_not_present(output_file):
    index_file = "../index.md"
    index_text = load_file(index_file).rstrip()

    output_name = os.path.basename(output_file)[:os.path.basename(output_file).rfind(".html")]
    if output_name not in index_text:
        index_text += "\n* [" + output_name + "](diaries/" + output_file + ")\n"
        write_to_file(index_file, index_text)

def run(args):
    #generate output file name
    output_file = os.path.basename(args.file)[:os.path.basename(args.file).rfind(".md")] + ".html"
    
    #copy and replace references
    updated_md = copy_and_replace_references(args.file)
    
    #write markdown updated to use new references
    write_to_file(args.file, updated_md)

    #call Markdown.pl to convert to HTML
    cmd = '%s %s > %s' % (args.convert_cmd, args.file, output_file)
    #cmd = "/contrib/projects/markdown/Markdown.pl " + file + " > " + output_file
    os.system(cmd)

    #add to index file, if not already present
    add_to_index_if_not_present(output_file)

    #if commit message given, commit everything to a git repo
    if args.message:
        os.chdir(args.git_repo_dir)
        cmd = "git add .; git commit -a -m '" + args.message + "'; git push origin master"
        os.system(cmd)

    #open the output in Chrome
    os.system("chrome " + output_file + "&")

if __name__ == "__main__": 
    run(parse_args(sys.argv[1:]))