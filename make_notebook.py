#!/usr/bin/python
import re
import os, shutil, sys
from ArgParser import *
import time

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

def get_references_to_replace(text, prefixes_to_exclude, repo_path):
    matches = re.findall("\[.*?\]\((.*?)\)", text)
    return filter(get_match_filter(prefixes_to_exclude, repo_path), matches)

def get_match_filter(prefixes_to_exclude, repo_path):
    def match_filter(match):
        return (not match.startswith(prefixes_to_exclude)
                and not os.path.abspath(match).startswith(repo_path))
    return match_filter

def copy_and_replace_references(entry_file, prefixes_to_exclude, repo_path):
    timestamp = time.strftime('%H:%M:%S')
    ref_folder = entry_file[:entry_file.find(".md")] + "-resources/" + timestamp
    os.makedirs(ref_folder)

    text = load_file(entry_file)

    for reference in get_references_to_replace(text, prefixes_to_exclude, repo_path):
        dst = ref_folder + "/" + os.path.basename(reference)
        shutil.copytree(reference, dst) if os.path.isdir(reference) else shutil.copyfile(reference, dst)
        text = text.replace(reference, os.path.relpath(dst, os.path.dirname(entry_file)))

    return text

def extract_title(md_text):
    prev = None
    for line in md_text.split('\n'):
        if line.startswith('-----------'):
            return prev
        prev = line
    return "Untitled"

def write_to_file(file, text):
    with open(file, 'w') as f:
        f.write(text)
    f.close()

def add_footer(html_file):
    os.system('cat footer.html >> %s' % (html_file))

def add_to_index_if_not_present(output_file, title, repo_path, convert_cmd):
    index_file = repo_path + "/index.md"
    index_text = load_file(index_file).rstrip()

    output_name = os.path.basename(output_file)[:os.path.basename(output_file).rfind(".html")]
    if output_name not in index_text:
        index_text += "\n* [" + output_name + ": " + title + "](" + output_file + ")\n"
        write_to_file(index_file, index_text)

        #convert index file to markdown
        cmd = '%s %s > %s' % (convert_cmd, index_file, index_file[:index_file.rfind(".md")]+".html")
        os.system(cmd)

def run(args):
    repo_path = os.path.abspath(args.git_repo_dir)
    entry_file = os.path.relpath(args.file, repo_path)

    output_file = entry_file[:entry_file.rfind(".md")] + ".html"
    
    #copy and replace references

    #prefixes_to_exclude = ('http://', 'https://', 'file:///')
    prefixes_to_exclude = ('http://', 'https://', '/data/', 'file:///')
    updated_md = copy_and_replace_references(entry_file, prefixes_to_exclude, repo_path)
    
    #write markdown updated to use new references
    write_to_file(args.file, updated_md)

    #call Markdown to convert to HTML
    cmd = '%s %s > %s' % (args.convert_cmd, args.file, output_file)
    os.system(cmd)
    add_footer(output_file)

    title = extract_title(updated_md)

    #add to index file, if not already present
    add_to_index_if_not_present(output_file, title, repo_path, args.convert_cmd)

    #if commit message given, commit everything to a git repo
    if args.message:
        os.chdir(repo_path)
        cmd = "git add .; git commit -a -m '" + args.message + "'; git push origin master"
        os.system(cmd)

    #open the output in Chrome
    os.system("chrome " + output_file + "&")

if __name__ == "__main__": 
    run(parse_args(sys.argv[1:]))
