#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <signal.h>

#define INFO_DIR "/tmp/mpvinfo/"
#define MAX_COL 50

void join_path(parent, child, dest)
  char *parent, *child, *dest;{
  strcpy(dest, parent);
  int l = strlen(dest);
  if (*(dest+l-1) == '/'){
    strcpy(dest+l, child);
  }else{
    *(dest+l) = '/';
    strcpy(dest+l+1, child);
  }
}

int main(int argc, char *argv[])
{
  DIR *dir;
  FILE *fp;
  char fullpath[128], c;
  struct dirent *file;
  if (access(INFO_DIR, F_OK)!=0){
    printf("No MPV instances.\n");
    return 0;
  }
  int count = 0, col, pid;
  dir = opendir(INFO_DIR);
  while ((file = readdir(dir)) != NULL){
    if(file->d_name[0]=='.'){
      continue;
    }
    join_path(INFO_DIR, file->d_name, fullpath);

    /* check if the instance is still running. */
    pid = atoi(file->d_name);
    if (kill(pid, 0)){
      remove(fullpath);
      continue;
    }
    count++;
    fp = fopen(fullpath, "r");
    printf("(%d) ", pid);
    col=0;
    while ((c=getc(fp))!=EOF){
      col++;
      if (c=='\n') col=0;
      if (col > MAX_COL){
	fputc('\n', stdout);
	fputc('\t', stdout);
	col = 0;
      }
      fputc(c, stdout);
    }
  }
  if (count==0){
    printf("No MPV instances.\n");
  }
  return 0;
}
