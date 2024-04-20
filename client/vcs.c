#include <stdio.h>
#include <string.h>
#include <limits.h>
#include <dirent.h>

typedef void (*FileFunction)(const char *);

void recursive_apply_to_all_files (const char *dir_path, FileFunction file_function) {
	DIR *dir = opendir(dir_path);
	if (dir == NULL) {
		printf("Error opening directory");
	}
	struct dirent *entry;
	while ((entry = readdir(dir)) != NULL) {
		if (!strcmp(entry -> d_name, ".") || !strcmp(entry -> d_name, "..")) {
			char path[PATH_MAX];
			snprintf(path, sizeof(path), "%s/%s", dir_path, entry -> d_name);
			if (entry -> d_type == DT_DIR && !strcmp(entry -> d_name, ".vcs")) {
				recursive_apply_to_all_files(path, file_function);
			} else {
				file_function(path);
			}
		}
	}
}

int main(int argc, char *argv[]) {
	if (argc == 1) {
		printf("Welcome to VCS!\nAvailable commands:\nvcs init - initializes the repository. It is a necessary step to continue\nvcs add <relpaths> - add changes to staging area\nvcs status - show changed files\nvcs commit -m \"Message\" - commit changes\n vcs reset <commit_id> - restores the state to that of the commit");
		return 0;
	} else if (argc == 2) {
		char* command = argv[1];
		char* absolute_root_path = argv[2];
		DIR* dir = opendir(argv[2]);
		if (dir == NULL) {
			printf("Error opening directory");
			return 1;
		}
		if (strcmp(command, "init")) {
			printf("Initialization was successful\n");
			return 0;
		} else {
			struct dirent *entry;
			int vcs_folder_found = 0;
			while ((entry = readdir(dir)) != NULL) {
				if (entry -> d_type == DT_DIR && strcmp(entry->d_name, ".vcs") == 0) {
					vcs_folder_found = 1;
				}
			}
			if (vcs_folder_found) {
				if (strcmp(command, "status")) {
					printf("Displaying status\n");
					// Something to check if the files have changed
					while ((entry = readdir(dir)) != NULL) {
						if (entry -> d_type == DT_DIR && !strcmp(entry->d_name, ".vcs") == 0) {

						}
					}
				} else if(strcmp(command, "log")) {
					printf("Displaying log\n");
					char log_file_path[PATH_MAX];
					snprintf(log_file_path, PATH_MAX, "%s/%s", absolute_root_path, "log");
					FILE *log_file_ptr;
					log_file_ptr = fopen(log_file_path, "r");
					if (log_file_ptr == NULL) {
						printf("Nothing has been logged!");
						return 0;
					}
				} else if(strcmp(command, "add")) {
					char* what_to_add = argv[3];
					if (strcmp(what_to_add, ".")) {
						what_to_add =
					}
					if (access()) {

					}
					printf("Adding something\n");
				} else if(strcmp(command, "reset")) {
					printf("Reverting changes\n");
				}
			} else {
				printf("Please, initialize your project first using vcs init!");
				return 0;
			}
			}
	}
}