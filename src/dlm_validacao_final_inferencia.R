suppressPackageStartupMessages(library(clubSandwich))
a <- commandArgs(trailingOnly=TRUE);root<-a[1];cache<-file.path(root,'data/interim/dlm_validacao_final');out<-file.path(root,'outputs/tables/dlm_validacao_final');m<-read.csv(file.path(cache,'manifest.csv'));result<-list();n<-0;previous<-file.path(out,'cr2.csv');if(file.exists(previous)){old<-read.csv(previous);old$q<-NULL;done<-unique(old$id);m<-m[!m$id%in%done,];result[[1]]<-old;n<-1}
for(i in seq_len(nrow(m))) {
 meta<-m[i,];d<-read.csv(file.path(cache,paste0(meta$id,'.csv')));zn<-grep('^z[0-9]+$',names(d),value=TRUE)
 fes<-if(meta$seasonal) c('factor(season)','factor(data_base)') else if(meta$regional) c('factor(uf)','factor(regtime)') else c('factor(uf)','factor(data_base)')
 stopifnot(all(d$peso==1));fit<-lm(reformulate(c(zn,fes),response='y'),data=d,weights=peso);if(anyNA(coef(fit))) {MM<-model.matrix(fit)[, !is.na(coef(fit)),drop=FALSE];DD<-data.frame(y=d$y,MM,check.names=TRUE);fit<-lm(reformulate(setdiff(names(DD),'y'),response='y',intercept=FALSE),data=DD,weights=d$peso)}
 expected<-read.csv(file.path(cache,paste0(meta$id,'.coef.csv')))$estimate;stopifnot(max(abs(coef(fit)[zn]-expected))<1e-8)
 V<-vcovCR(fit,cluster=d$uf,type='CR2',inverse_var=TRUE);cm<-read.csv(file.path(cache,paste0(meta$id,'.contrasts.csv')))
 scalar<-cm[cm$endpoint!='joint',];CC<-matrix(0,nrow(scalar),length(coef(fit)),dimnames=list(NULL,names(coef(fit))));CC[,zn]<-as.matrix(scalar[,zn,drop=FALSE])
 ww<-linear_contrast(fit,vcov=V,contrasts=CC,test='Satterthwaite',p_values=TRUE)
 rr<-data.frame(endpoint=scalar$endpoint,estimate=ww$Est,se=ww$SE,df=ww$df,low=ww$CI_L,high=ww$CI_U,p=ww$p_val)
 jj<-cm[cm$endpoint=='joint',];CC<-matrix(0,nrow(jj),length(coef(fit)),dimnames=list(NULL,names(coef(fit))));CC[,zn]<-as.matrix(jj[,zn,drop=FALSE])
 tt<-tryCatch(Wald_test(fit,constraints=CC,vcov=V,test='HTZ'),error=function(e)NULL)
 joint<-data.frame(endpoint='joint',estimate=NA,se=NA,df=if(is.null(tt))NA else as.numeric(tt$df_denom),low=NA,high=NA,p=if(is.null(tt))NA else as.numeric(tt$p_val))
 rr<-rbind(rr,joint);rr$status<-ifelse(is.na(rr$p)|is.na(rr$df)|rr$df<=0,'indisponível','calculado');rr$p[rr$status=='indisponível']<-NA
 n<-n+1;result[[n]]<-cbind(meta,rr)
 tmp<-file.path(out,'cr2.tmp');write.csv(do.call(rbind,result),tmp,row.names=FALSE);file.rename(tmp,file.path(out,'cr2.csv'));cat('CR2',i,meta$id,'\n');flush.console()
}
writeLines(capture.output(sessionInfo()),file.path(out,'r_session.txt'))
