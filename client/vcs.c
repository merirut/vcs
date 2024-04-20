#include <stdio.h>

int main(int argc, char *argv[]) {
	if (argc == 1) {
		printf("Welcome to VCS!\nAvailable commands:\nvcs init - initializes the repository. It is a necessary step to continue\nvcs add <relpaths> - add changes to staging area\nvcs status - show changed files\nvcs commit -m \"Message\" - commit changes\n vcs reset <commit_id> - restores the state to that of the commit");
		return 0;
	} else if (argc == 2) {
		char* command = argv[1];
		if (strcmp(command, "init")) {
			printf("Initialization was successful");
		} else if (strcmp(command, "status")) {
			printf("Displaying status");
		} else if(strcmp(command, "log")) {
			printf("Displaying log");
		} else if(strcmp(command, "add")) {
			printf("Adding something");
		} else if(strcmp(command, "reset")) {
			printf("Reverting changes");
		}
	}
}