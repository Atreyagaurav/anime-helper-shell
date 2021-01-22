// Build with: gcc -o plugin.so plugin.c `pkg-config --cflags mpv --libs libnotify` -shared -fPIC
// Warning: do not link against libmpv.so! Read:
//    https://mpv.io/manual/master/#linkage-to-libmpv
// The pkg-config call is for adding the proper client.h include path.

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sys/stat.h>
#include <unistd.h>
#include <time.h>

#include <mpv/client.h>
#include <libnotify/notify.h>
#include <libnotify/notification.h>

#define INFO_DIR "/tmp/mpvinfo/"
#define LOGGING_OFF 0 		/* change it to 1 to turn off logging */
#define LOG_FILE "/home/gaurav/.log/mpv.log"

#define MAX_CHAR 50

struct status {
  char *fname;
  double cur, dur, perc;
} st = {.fname=NULL};


void write_time(FILE *fp, int time_sec){
  if (time_sec < 60*60){
    fprintf(fp, "%02d:%02d", time_sec/60, time_sec % 60);
  }else{
    fprintf(fp, "%d:%02d:%02d", time_sec/3600 ,(time_sec%3600)/60, time_sec % 60);
  }
}

void shorten_string(char *str, int len){
  int total;
  total = strlen(str);
  if(total < len){
    return;
  }
  int i, pre, post;
  pre = len * 3 / 4;
  post = len - pre - 3;
  for(i=0; i<3; i++){
    *(str+pre+i)= '.';
  }
  strcpy(str+pre+3,str+total-post);
}

void info_filename(int number, char *dest){
  strcpy(dest, INFO_DIR);
  char count[5];
  int i;
  count[4] = '\0';
  for(i=3;i>=0;i--){
    count[i] = number % 10 + '0';
    number /= 10;
  }
  int l = strlen(dest);
  if (*(dest+l-1) == '/'){
    strcpy(dest+l,count);
  }else{
    *(dest+l) = '/';
    strcpy(dest+l+1, count);
  }
}

void new_info_file(char *filename){
  int i = 1;
  while (1){
    info_filename(i++, filename);
    if (access(filename, F_OK) == 0){
      continue;
    }
    return;
  }
}


void read_status(mpv_handle * handle){
  /* if (st.fname != NULL) mpv_free(&(st.fname)); */
  mpv_get_property(handle, "media-title", MPV_FORMAT_STRING, &(st.fname));
  mpv_get_property(handle, "time-pos", MPV_FORMAT_DOUBLE, &(st.cur));
  mpv_get_property(handle, "duration", MPV_FORMAT_DOUBLE, &(st.dur));
  mpv_get_property(handle, "percent-pos", MPV_FORMAT_DOUBLE, &(st.perc));
}


void write_status(char *filename, mpv_handle *handle){
  FILE *fp;
  /* char fname[MAX_CHAR+1]; */
  /* shorten_string(st.fname, MAX_CHAR); */
  fp = fopen(filename, "w");
  fprintf(fp,"%s\n    TIME:",st.fname);
  write_time(fp, (int)st.cur);
  fprintf(fp," of ");
  write_time(fp, (int)st.dur);
  fprintf(fp,"(%.2f%%)\n", st.perc);
  fclose(fp);
}

void send_notification(NotifyNotification *n){
  notify_notification_update(n, "New Media Start", st.fname, NULL);
  notify_notification_show(n, NULL);
}

void clear_status(char *filename) {
  remove(filename);
}

void write_log(const char *action){
  if (LOGGING_OFF) return;
  FILE *fp;
  time_t t1;
  t1 = time(NULL);
  fp = fopen(LOG_FILE, "a");
  fprintf(fp, "%ld %s ",t1,action);
  write_time(fp, (int)st.cur);
  fprintf(fp, " ");
  write_time(fp, (int)st.dur);
  fprintf(fp," %s\n",st.fname);
  fclose(fp);
}

void init_plugin(mpv_handle *handle, char *filename, NotifyNotification **n){
    mkdir(INFO_DIR, 0700);
    new_info_file(filename);
    printf("Status Update file: %s\n", filename);
    printf("Log file: %s\n", LOG_FILE);
    mpv_observe_property(handle, 0, "playback-time", MPV_FORMAT_DOUBLE);
    mpv_observe_property(handle, 0, "pause", MPV_FORMAT_FLAG);
    notify_init("MPV");
    *n = notify_notification_new("Init", NULL, NULL);
    notify_notification_set_urgency(*n, NOTIFY_URGENCY_LOW);
}

void exit_plugin(mpv_handle *handle, char *filename, NotifyNotification *n) {
  clear_status(filename);
  g_object_unref(G_OBJECT(n));
  notify_uninit();
}

int handle_event(mpv_handle *handle, mpv_event *event, char *filename, NotifyNotification *n, int *started, int *on_seek){
    mpv_event_property *prop;
    switch (event->event_id){
	case MPV_EVENT_SHUTDOWN:
	  return 0;
	  break;
	case MPV_EVENT_FILE_LOADED:
	  *started = 1;
	  read_status(handle);
	  send_notification(n);
	  write_log(mpv_event_name(event->event_id));
	  break;
	case MPV_EVENT_END_FILE:
	  if (*started==0) return 1;
	  *started = 0;
	  write_log(mpv_event_name(event->event_id));
	  break;
	case MPV_EVENT_SEEK:
	  if (*on_seek) return 1;
	  *on_seek = 1;
	  write_log(mpv_event_name(event->event_id));
	  break;
	case MPV_EVENT_PLAYBACK_RESTART:
	  if (*on_seek == 0) return 1;
	  *on_seek = 0;
	  read_status(handle);
	  write_log(mpv_event_name(event->event_id));
	  break;
	case MPV_EVENT_PROPERTY_CHANGE:
	  prop = (mpv_event_property *)event->data;
	  if (strcmp(prop->name, "playback-time") == 0) {
	    read_status(handle);
	    write_status(filename, handle);
	  }else if (strcmp(prop->name, "pause") == 0) {
	    if (*started) write_log(*(int*)prop->data ? "pause":"unpause");
	  }
	  break;
	default:
	  break;
	}
    return 1;
}


int mpv_open_cplugin(mpv_handle *handle)
{
    char filename[128];
    int flag;
    int on_seek = 0, started = 0;
    NotifyNotification *n;
    init_plugin(handle, filename, &n);
    do{
        mpv_event *event = mpv_wait_event(handle, -1);
	flag = handle_event(handle, event, filename, n, &started, &on_seek);
    }while (flag);
    exit_plugin(handle, filename, n);
    return 0;
}

