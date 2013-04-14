#include <stdio.h>
#include <string.h>
#include <math.h>
#define MAXGOODTCAL 400
#define MAXGOODTSYS 4000

int main(int argc, char*argv[])
{
  FILE  *infile;
  char   keyword[120], stringvalue[120], sourcename[20];
  char   scantype[9],scantypetemp[9];
  long   intvalue, scannum, channelnum;
  double doublevalue, scanfraction;
  long   sourcecount=0, headercount=0;
  long   noint,i,n_on,n_off;
  long   hour,minute,second;
  double datatotal,dataontotal,dataofftotal;
  long   year, month, day;
  double hot, cold, sky, tcal, stsys, mmh2o, el, tamb;
  double voidval=0.0;

  if (argc!=2){
    printf("Usage: %s filename\n",argv[0]);
    return;
  }

  infile=fopen(argv[1],"r");
  while (fscanf(infile,"%s",keyword)==1){
    if (strcmp(keyword,"obsmode")==0){
      fscanf(infile,"%s",scantypetemp);
      if (strstr(scantypetemp,"2")==NULL){
	strcpy(scantype,scantypetemp);
      }
    }
    if (strcmp(keyword,"source")==0){
      fscanf(infile,"%s",sourcename);
      sourcecount++;
    }
    if (strcmp(keyword,"header:")==0){
      headercount++;
      // The word "data" appears here too; make sure we're past this
    }
    if (strcmp(keyword,"tcal")==0){
      fscanf(infile,"%lf",&tcal);
    }
    if (strcmp(keyword,"tamb")==0){
      fscanf(infile,"%lf",&tamb);
    }
    if (strcmp(keyword,"el")==0){
      fscanf(infile,"%lf",&el);
    }
    if (strcmp(keyword,"stsys")==0){
      fscanf(infile,"%lf",&stsys);
    }
    if (strcmp(keyword,"mmh2o")==0){
      fscanf(infile,"%lf",&mmh2o);
    }
    if (strcmp(keyword,"ut")==0){
      fscanf(infile,"%lf",&doublevalue);
      if (doublevalue<25.0){
	hour = lrint(trunc(doublevalue));
	doublevalue -= hour;
	doublevalue *= 60.0;
	minute = lrint(trunc(doublevalue));
	doublevalue -= minute;
	doublevalue *= 60.0;
	second = lrint(doublevalue);
      }
    }
    if (strcmp(keyword,"utdate")==0){
      fscanf(infile,"%lf",&doublevalue);
      //fprintf(stderr, "%lf ",doublevalue);
      year = lrint(trunc(doublevalue));
      doublevalue -= year;
      doublevalue *= 100.0;
      month = lrint(trunc(doublevalue));
      doublevalue -= month;
      doublevalue *= 100.0;
      doublevalue += 0.01; // avoid truncation error
      day = lrint(trunc(doublevalue));
      //fprintf(stderr,"%li %li %li\n",year,month,day);
    }
    if (strcmp(keyword,"noint")==0){
      fscanf(infile,"%lf",&doublevalue);
      noint = lrint(doublevalue);
    }
    if (strcmp(keyword,"scan")==0){
      fscanf(infile,"%lf",&doublevalue);
      scannum = lrint(doublevalue);
      doublevalue -= scannum;
      doublevalue *= 100;
      channelnum = lrint(doublevalue);
    }
    if ((strcmp(keyword,"data")==0)&&(sourcecount==headercount)){
      dataontotal  = 0.0;
      dataofftotal = 0.0;
      datatotal    = 0.0;
      n_on         = 0;
      n_off        = 0;

      if (strcmp(scantype,"CONTSEQ")==0){
	for (i=0;i<noint;i++){
	  fscanf(infile,"%lf",&doublevalue);
	  if (i%8==1 || i%8==2 || i%8==4 || i%8==7){
	    dataontotal += doublevalue;
	    n_on++;
	  }
	  else{
	    dataofftotal += doublevalue;
	    n_off++;
	  }
	}
	dataontotal  /= n_on;
	dataofftotal /= n_off;
	if (dataontotal>0 && dataofftotal>0 && tcal<(MAXGOODTCAL) && stsys<(MAXGOODTSYS)) {
	  printf("Scan %li %04li-%02li-%02li %02li:%02li channel %li %-8s %-8s  data on   %8.1lf off  %8.1lf void %8.1lf tcal %6.2lf tsys %6.2lf pwv %5.3lf el %4.1lf tamb %5.1lf\n",scannum,year,month,day,hour,minute,channelnum,sourcename,scantype,dataontotal,dataofftotal,voidval,tcal,stsys,mmh2o,el,tamb);
	}
      } // end if CONTSEQ block

      if ((strcmp(scantype,"CONTQK5")==0)||(strcmp(scantype,"CONTFIVE")==0)){
	for (i=0;i<noint;i++){
	  fscanf(infile,"%lf",&doublevalue);
	  if ((i>=16)&&(i<24)){  // only pick central pointing
	    if (i%8==1 || i%8==2 || i%8==4 || i%8==7){
	      dataontotal += doublevalue;
	      n_on++;
	    }
	    else{
	      dataofftotal += doublevalue;
	      n_off++;
	    }
	  }
	}
	dataontotal  /= n_on;
	dataofftotal /= n_off;
	if (dataontotal>0 && dataofftotal>0 && tcal<(MAXGOODTCAL) && stsys<(MAXGOODTSYS)){
	  printf("Scan %li %04li-%02li-%02li %02li:%02li channel %li %-8s %-8s  data on   %8.1lf off  %8.1lf void %8.1lf tcal %6.2lf tsys %6.2lf pwv %5.3lf el %4.1lf tamb %5.1lf\n",scannum,year,month,day,hour,minute,channelnum,sourcename,scantype,dataontotal,dataofftotal,voidval,tcal,stsys,mmh2o,el,tamb);
	}
      } // end if CONTQK5 or CONTFIVE block


      if (strcmp(scantype,"CONTCOLD")==0){
	if (noint>3){
	  printf("#More than 3 data points on COLD scan\n");
	}
	fscanf(infile,"%lf",&hot);
	fscanf(infile,"%lf",&cold);
	fscanf(infile,"%lf",&sky);
	if ((hot>0)&&(cold>0)&&(sky>0)){
	  printf("Scan %li %04li-%02li-%02li %02li:%02li channel %li %-8s %-8s  data vane %8.1lf cold %8.1lf sky  %8.1lf tcal %6.2lf tsys %6.2lf pwv %5.3lf el %4.1lf tamb %5.1lf\n",scannum,year,month,day,hour,minute,channelnum,sourcename,scantype,hot,cold,sky,tcal,stsys,mmh2o,el,tamb);
	}
      } // end if CONTCOLD


      if (strcmp(scantype,"CONTCAL")==0){
	dataontotal = 0;
	dataofftotal = 0;
	n_on = 0;
	n_off = 0;
        if (noint>2){
	  printf("# %li\n",noint);
	}
	for (i=0;i<noint;i++){
	  fscanf(infile,"%lf",&doublevalue);
	  if (i%2==0){
	    dataontotal += doublevalue;
	    n_on++;
	  }
          else {
	    dataofftotal += doublevalue;
	    n_off++;
	  }
	}	
	dataontotal  /= n_on;
	dataofftotal /= n_off;
	if (dataontotal>0 && dataofftotal>0 && tcal<(MAXGOODTCAL) && stsys<(MAXGOODTSYS)){
	  printf("Scan %li %04li-%02li-%02li %02li:%02li channel %li %-8s %-8s  data vane %8.1lf sky  %8.1lf void %8.1lf tcal %6.2lf tsys %6.2lf pwv %5.3lf el %4.1lf tamb %5.1lf\n",scannum,year,month,day,hour,minute,channelnum,sourcename,scantype,dataontotal,dataofftotal,voidval,tcal,stsys,mmh2o,el,tamb);
	}

      } // end if CONTCAL      


    }
  }
  fclose(infile);
}
