suppressPackageStartupMessages(library(clubSandwich))
args<-commandArgs(trailingOnly=TRUE);root<-args[1];cache<-file.path(root,'data/interim/dlm_classico');out<-file.path(root,'outputs/tables/dlm_classico');m<-read.csv(file.path(cache,'manifest.csv'));result<-list();n<-0
previous<-file.path(out,'cr2.csv');if(file.exists(previous)){old<-read.csv(previous);old$q<-NULL;done<-unique(old$id);m<-m[!m$id%in%done,];result[[1]]<-old;n<-1}
for(i in seq_len(nrow(m))){
 meta<-m[i,];d<-read.csv(file.path(cache,paste0(meta$id,'.csv')));zn<-grep('^z[0-9]+$',names(d),value=TRUE)
 fit<-lm(reformulate(c(zn,'factor(uf)','factor(data_base)'),response='y'),data=d);expected<-read.csv(file.path(cache,paste0(meta$id,'.coef.csv')))$estimate
 stopifnot(!anyNA(coef(fit)),max(abs(coef(fit)[zn]-expected))<1e-8)
 V<-vcovCR(fit,cluster=d$uf,type='CR2',inverse_var=TRUE);cm<-read.csv(file.path(cache,paste0(meta$id,'.contrasts.csv')));CC<-matrix(0,nrow(cm),length(coef(fit)),dimnames=list(NULL,names(coef(fit))));CC[,zn]<-as.matrix(cm[,zn,drop=FALSE])
 w<-linear_contrast(fit,vcov=V,contrasts=CC,test='Satterthwaite',p_values=TRUE);rr<-data.frame(endpoint=cm$endpoint,estimate=w$Est,se=w$SE,df=w$df,low=w$CI_L,high=w$CI_U,p=w$p_val)
 C<-matrix(0,length(zn),length(coef(fit)),dimnames=list(NULL,names(coef(fit))));C[,zn]<-diag(length(zn));tt<-tryCatch(Wald_test(fit,constraints=C,vcov=V,test='HTZ'),error=function(e)NULL)
 rr<-rbind(rr,data.frame(endpoint='joint',estimate=NA,se=NA,df=if(is.null(tt))NA else as.numeric(tt$df_denom),low=NA,high=NA,p=if(is.null(tt))NA else as.numeric(tt$p_val)));rr$status<-ifelse(is.na(rr$p)|is.na(rr$df)|rr$df<=0,'indisponível','calculado');rr$p[rr$status=='indisponível']<-NA
 n<-n+1;result[[n]]<-cbind(meta,rr);tmp<-file.path(out,'cr2.tmp');write.csv(do.call(rbind,result),tmp,row.names=FALSE);file.rename(tmp,previous);cat('CR2',i,meta$id,'\n');flush.console()
}
writeLines(capture.output(sessionInfo()),file.path(out,'r_session.txt'))
