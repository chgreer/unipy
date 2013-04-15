#include <stdlib.h>
#include <errno.h>
#include <stdio.h>
#include <sys/io.h>
#include <math.h>
#include <string.h>
#include <sched.h>
#include <fcntl.h>
#define PI 3.1415926536
#define TWOPI 6.28318530717958
#define NTER 1

void plotf(int,int,double *, double *);
double saturn(double *,double);
static double tim[100000],pdata[100000];
char fname[256];
int tstart, tstop, ttstart, ttstop;
int mode;
int main(int argc, char *argv[])
{
    char buf[32768],ttyp[256],ttyp2[256];
    int i,j,line,line2,np,dday,hr,min,hlen,dlen;
    double dy,fday,scan,scanp,tsat,h,tsatt;
    double r,tamb,tsys,freq;
    double pvane;
    double pmax,pmin;
    double sonn,nss;

typedef struct {
     int numrec,numdata,bytes_per_rec,bytes_per_index,num_used,counter,sddtyp,sddver,pad[512];
} sddtype;
    sddtype bt;
typedef struct {
     int scanstart,scanstop;
     float hor,vert;
     char scan[16];
     float scannum,fres;
     double restfreq;
     float lst,utdate;
     short mode,recnum,poscode,pad[512];
} sdditype;
   sdditype in;

typedef struct {
     short numclass,classstart[15];
} sddctype;
   sddctype sc;

double data[1024];
float sdata[2048];

    FILE *file1;
    mode=0;
 if (argc > 1) sscanf(argv[1], "%s", fname);
 for(i=0;i<argc;i++){
  sscanf(argv[i], "%79s", buf);
  if (strstr(buf, "-mode")) { sscanf(argv[i+1], "%d",&mode);}
 }
    if ((file1 = fopen(fname, "r")) == NULL) {
        printf("cannot open file:%s\n", fname);
        return 0;
    }
    line = line2 = 0; scanp=0; np=0;
    pmax = -1e99;
    pmin = 1e99;
    pvane=0;
    printf("file %s\n", fname);
    bt.numrec=0;
    fread(&bt,512,1,file1);
    printf("numrec %d numdata %d bytes_per_rec %d bytes_per_index %d num_used %d counter %d sddtyp %d sddver %d pad %d\n",
             bt.numrec,bt.numdata,bt.bytes_per_rec,bt.bytes_per_index,bt.num_used,bt.counter,bt.sddtyp,bt.sddver,bt.pad[0]);
    i=0;
    while(!feof(file1) && i < bt.numrec){
        fread(&in,64,1,file1);
        //printf("i %d start %d stop %d source %.6s obscode %d\n",i,in.scanstart,in.scanstop,in.scan,in.mode-256);
        fclose(file1);
        if ((file1 = fopen(fname, "r")) == NULL) {
            printf("cannot open file:%s\n", fname);
            return 0;
        }
        for(j=0;j<in.scanstart-1;j++) fread(data,512,1,file1);
        fread(&sc,32,1,file1);
        fread(data,8,1,file1);
        hlen = data[0];
        //printf("hlen %d sc.classstart[0] %d\n",hlen,sc.classstart[0]);
        fread(&data[1],hlen-8-32,1,file1);
        hr = (int)(data[sc.classstart[2]-5+1]);
        min = (data[sc.classstart[2]-5+1] - hr)*60.0;
        dlen = data[sc.classstart[0]-5+1];
        printf("%9.4f %02d:%02d %.8s scan %3.0f tsys %3.0f tamb %3.0f opac %5.3f el %3.0f %.8s %.8s\n",
	     data[sc.classstart[2]-5],     // yyyy.mmdd
	     hr,min,
	     in.scan,                      // source name
	     data[sc.classstart[0]-5+2],   // scan number
	     data[sc.classstart[11]-5+6],  // tsys (K)
	     data[sc.classstart[4]-5+0],   // tamb (K)
	     data[sc.classstart[11]-5+16], // opacity -- ignore this
	     data[sc.classstart[3]-5+10],  // elevation (deg)
	     (char*)&data[sc.classstart[0]-5+8+2], // type of scan
	     (char*)&data[sc.classstart[0]-5+9+2]  // receiver
//                  (char*)&data[sc.classstart[11]-5+22]
                  );
     if((strstr(in.scan,"SATURN") || (strstr(in.scan,"aturn")))) {
//      for(j=0;j<25;j++) printf("class6 %d %f\n",j,data[sc.classstart[5]-5+j]);
      fread(sdata,dlen,1,file1);
      pmax = -1e99; pmin = 1e99;
      for(j=0;j<dlen/4;j++){
      if(fabs(data[sc.classstart[0]-5+2] - 44)< 1.0) {
           printf("j %d data %e\n",j,sdata[j]);
           tim[j] = j;
           pdata[j] = sdata[j]*1e-3;     
           if(sdata[j] > 0.0) np = j;
      }
 if(strstr((char*)&data[sc.classstart[0]-5+8+2],"CONTSEQ"))
        printf("CONTSEQ j %d data %8.1f scan %3.0f\n",j,sdata[j]*1e-3,data[sc.classstart[0]-5+2]);
        if(sdata[j] > pmax) pmax = sdata[j];
        if(sdata[j] < pmin && sdata[j] > 0.0) pmin = sdata[j];
      }
     sonn = 0; nss=0;
     for(j=0;j<dlen/4;j++){
     if(strstr((char*)&data[sc.classstart[0]-5+8+2],"CONTSEQ")) {
     if(j%8==1 || j%8==2 || j%8==4 || j%8==7) {sonn += sdata[j]; nss++;}
     else sonn += -sdata[j];
     }
     if(strstr((char*)&data[sc.classstart[0]-5+8+2],"CONTFIVE")&& j >=16 && j<= 23) {
     if(j%8==1 || j%8==2 || j%8==4 || j%8==7) {sonn += sdata[j]; nss++;}
     else sonn += -sdata[j];
     }
     }
     freq = data[sc.classstart[11]-5]*1e-3;
     tsat = saturn(&h,freq);
     tsatt = (pmax-pmin)*1e-3;
     if(nss > 0){
     tsatt = sonn*1e-3 / nss;
     if(pmax > 50e3 && pmax < 1000e3 && (!strstr((char*)&data[sc.classstart[0]-5+8+2],"CONTSTIP")))
        printf("SATURN %9.4f %02d:%02d scan %3.0f flux %5.0f freq %3.0f eff %5.0f %.8s %.8s tsys %3.0f el %3.0f\n",
                 data[sc.classstart[2]-5],hr,min,data[sc.classstart[0]-5+2],
                 h,freq,tsatt*50.0/tsat,
                 (char*)&data[sc.classstart[0]-5+8+2],
                 (char*)&data[sc.classstart[0]-5+9+2],data[sc.classstart[11]-5+6],data[sc.classstart[3]-5+10]
                 );
        }
      }
      fclose(file1);
      if ((file1 = fopen(fname, "r")) == NULL) {
        printf("cannot open file:%s\n", fname);
        return 0;
       }
      for(j=0;j<i;j++) fread(&in,64,1,file1);
     i++;
    }
    fclose(file1);
    if(np > 0) plotf(np,44,tim,pdata);
}


double saturn(double *flux,double freq)
{
    double bw,sd,a,bfc,h,tsat,wav;
    wav = 300.0*1e-3/freq;
    bw = 1.22 * wav / 10;
    sd = 9.7/(57.3*3600.0);  // semidiam Saturn
    a = 4.0*log(2.0)*sd*sd/(bw*bw); // Argument of exp()
    bfc = a/(1.0-exp(-a)); // Beam filling correction, dimensionless
    h = 2.0*1.38e-23*100.0*3.14*sd*sd/(1.3e-3*1.3e-3);  // 100 K brightness
    h = h / bfc;
    tsat = 0.5 * 3.1415 * 5.0 * 5.0 * h / (2.0 * 1.38e-23); // 50% eff 10m dish
    *flux = h*1e26;
    return tsat; 
}


void plotf(int np, int day, double tim[], double data[])
{
    char txt[256];
    int k, j1, j2, iter;
    double h,s,b,x, y, xp, yp, dmax, dmin, dd, f, totpp, err;
    double xoffset,yoffset;
    double tsat;
    FILE *file;

    if ((file = fopen("spe.pos", "w")) == NULL) {
        printf("cannot open spe.pos:\n");
        return;
    }
    fprintf(file, "%%!PS-Adobe-\n%c%cBoundingBox:  0 0 612 792\n%c%cEndProlog\n", '%', '%', '%', '%');
    fprintf(file, "1 setlinewidth\n");
    fprintf(file, "/Times-Roman findfont\n 12 scalefont\n setfont\n");

    xoffset = 80.0;
    yoffset = 100.0;
    dmax = -1.0e99;
    dmin = 1e99;
    for (k = 0; k < np; k++) {
          if(data[k] > dmax) dmax = data[k];
          if(data[k] < dmin) dmin = data[k];
    }
    b = (1.2 * 1.3e-3 /10.0) * 57.3 * 3600.0;
    s = 10.0/(57.3*3600.0);
    h = 2.0*1.38e-23*150.0*3.14*s*s/(1.3e-3*1.3e-3);
    tsat = 0.5 * 3.1415 * 5.0 * 5.0 * h / (2.0 * 1.38e-23);
//    printf("ratio %f %f b %f %e\n",dmax/dmin,tsat,b,h);
    dd = 0.0;
    j1 = 0;
    j2 = np;
    for(iter=0;iter<NTER;iter++){
    for (y = 0; y < 2; y++) 
    fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n 0 0 0 sethsbcolor stroke\n",
             xoffset, y * 200 + yoffset+iter*200, xoffset + 400.0, y * 200 + yoffset+iter*200);
    fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n 0 0 0 sethsbcolor stroke\n",
      xoffset, yoffset+iter*200, xoffset, 200.0 + yoffset+iter*200);
    fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n 0 0 0 sethsbcolor stroke\n",
      xoffset + 400.0, yoffset+iter*200, xoffset + 400.0, 200.0+yoffset+iter*200);
    fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n 0 0 0 sethsbcolor stroke\n",
     xoffset + 0.0, yoffset+iter*200, xoffset + 0.0, 200.0+yoffset+iter*200);
    }
    h=s=b=0;
    yp = 0;
    xp = 0;
    totpp = 0;
    for(iter=0;iter<NTER;iter++){
    for (k = 0; k < np; k++) {
        x = (tim[k]-tim[0]) * 400.0/(tim[np-1]-tim[0]);
       totpp = data[k];
        y = (totpp-dmin) * 200.0/ (dmax-dmin);
// printf("x %f y %f\n",x,y);
//        if (y < 0) y = 0;
        if (y > 200)
            y = 200;
            y += iter*200;
            yp=y;
            if(iter==0) err=0.1;
            if(iter==1) err=0.1;
            fprintf(file, "newpath\n %5.1f %5.1f %5.1f 0 360 arc\n closepath\n stroke\n" ,x + xoffset,y + yoffset,1.0);
            fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n %5.3f %5.3f %5.3f sethsbcolor stroke\n",
               x + xoffset,y+err + yoffset,x + xoffset, y-err + yoffset,h,s,b);
            fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n %5.3f %5.3f %5.3f sethsbcolor stroke\n",
               x -4 + xoffset,y+err + yoffset,x + 4 + xoffset, y+err + yoffset,h,s,b);
            fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n %5.3f %5.3f %5.3f sethsbcolor stroke\n",
               x -4 + xoffset,y-err + yoffset,x + 4 + xoffset, y-err + yoffset,h,s,b);
    } 
    }

    for (f = tim[0]; f <= tim[np-1]; f += (tim[np-1]-tim[0])*0.2) {
        x = (f-tim[0]) * 400.0 / (tim[np-1]-tim[0]);
        y = 0.0;
        fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n 0 0 0 sethsbcolor stroke\n",
         x + xoffset,y+yoffset,x + xoffset,y - 10.0+yoffset);
           sprintf(txt, "%f", f);
        fprintf(file, "%6.2f %6.2f moveto\n (%s) show\n",x + xoffset - 10.0,y - 20.0+yoffset, txt);
    } 
    for(iter=0;iter<NTER;iter++){
    for (f = dmin; f < dmax; f += (dmax-dmin)*0.2) {
        x = 0;
        y = (f-dmin) * 200.0 / (dmax-dmin);
        fprintf(file, "newpath\n %6.2f %6.2f moveto\n %6.2f %6.2f lineto\n 0 0 0 sethsbcolor stroke\n",
           x + xoffset,y+yoffset,x + xoffset + 5,y+yoffset);
         sprintf(txt, "%4.2f", f);
        fprintf(file, "%6.2f %6.2f moveto\n (%s) show\n",x + xoffset - 26.0,y -4.0+yoffset, txt);

    }
    sprintf(txt, "pwr");
    fprintf(file, "%6.2f %6.2f moveto\n 90 rotate\n (%s) show\n -90 rotate\n",xoffset -30.0, 265.0 - 100.0, txt);
    sprintf(txt, "pwr");
    }
    sprintf(txt, "fraction of day  - scan %d",mode);
    fprintf(file, "%6.2f %6.2f moveto\n (%s) show\n",xoffset + 180.0, 60.0, txt);
    sprintf(txt, "file: %s", fname);
    fprintf(file, "%6.2f %6.2f moveto\n (%s) show\n",380.0+xoffset, 50.0, txt);
    fprintf(file, "showpage\n%c%cTrailer\n", '%', '%');
    fclose(file);
} 

