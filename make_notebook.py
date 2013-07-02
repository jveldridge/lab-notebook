import re
import os, shutil, sys

def load_file(file):
	with open(file) as f:
		return f.read()

def get_references(text):
	return [match for match in re.findall("\[.*?\]\((.*?)\)", text) if not match.startswith(('http://', 'https://'))]

def copy_and_replace_references(file):
	ref_folder_name = os.path.basename(file)[:os.path.basename(file).find(".md")] + "-resources"
	ref_folder_path = os.path.dirname(os.path.abspath(file)) + '/' + ref_folder_name
	
	if not os.path.exists(ref_folder_path):
		os.mkdir(ref_folder_path)

	text = load_file(file)

	for reference in get_references(text):
		dst = ref_folder_path + "/" + os.path.basename(reference)
		shutil.copyfile(reference, dst)
		text = text.replace(reference, dst)

	return text

def write_to_file(file, text):
	with open(file, 'w') as f:
		f.write(text)
	f.close()

def run(file, git_repo_dir, commit_message):
	#generate output file name
	output_file = os.path.basename(file)[:os.path.basename(file).rfind(".md")] + ".html"
	
	#copy and replace references
	updated_md = copy_and_replace_references(file)
	
	#write markdown updated to use new references
	write_to_file(file, updated_md)

	#call Markdown.pl to convert to HTML
	cmd = "/contrib/projects/markdown/Markdown.pl " + file + " > " + output_file
	os.system(cmd)

	#commit everything to a git repo
	os.chdir(git_repo_dir)
	cmd = "git add .; git commit -a -m '" + commit_message + "'; git push origin master"
	os.system(cmd)

	#open the output in Chrome
	#os.system("chrome " + output_file + "&")

if __name__ == "__main__": 
    run(sys.argv[1], sys.argv[2])