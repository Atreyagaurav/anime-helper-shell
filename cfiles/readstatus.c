#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>

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
  int count = 0, col;
  dir = opendir(INFO_DIR);
  while ((file = readdir(dir)) != NULL){
    if(file->d_name[0]=='.'){
      continue;
    }
    count++;
    join_path(INFO_DIR, file->d_name, fullpath);
    fp = fopen(fullpath, "r");
    printf("(%d) ",count);
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
