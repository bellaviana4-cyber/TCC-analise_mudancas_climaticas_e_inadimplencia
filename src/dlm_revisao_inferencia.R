# CR2 generalizado com FE explícitos; Satterthwaite e HTZ. Sem fórmulas ad hoc.
suppressPackageStartupMessages(library(clubSandwich))
suppressPackageStartupMessages(library(plm))
args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)>0) args[1] else '.'
cache <- file.path(root,'data/interim/dlm_revisao')
out <- file.path(root,'outputs/tables/dlm_revisao')
manifest <- read.csv(file.path(cache,'r_manifest.csv'),check.names=FALSE)
results <- list(); counter <- 0
if(length(args)>1) {
 manifest <- manifest[manifest$design==args[2],]
 old <- read.csv(file.path(out,"cr2.csv"),check.names=FALSE)
 old <- old[old$design!=args[2],]
 old <- old[,setdiff(names(old),"q_global_p")]
 if(nrow(old)>0) {results[[1]] <- old; counter <- 1}
}
for(i in seq_len(nrow(manifest))) {
 meta <- manifest[i,]; dat <- read.csv(file.path(cache,paste0(meta$id,'.csv')))
 zn <- grep('^z[0-9]+$',names(dat),value=TRUE)
 fit <- lm(reformulate(c(zn,'factor(uf)','factor(data_base)'),response='y'),data=dat)
 V <- vcovCR(fit,cluster=dat$uf,type='CR2')
 cm <- read.csv(file.path(cache,paste0(meta$id,'.contrasts.csv')),check.names=FALSE)
 expected <- as.numeric(read.csv(file.path(cache,paste0(meta$id,'.coef.csv')))$estimate)
 stopifnot(max(abs(coef(fit)[zn]-expected))<1e-8)
 for(ep in unique(cm$endpoint)) {
  z <- cm[cm$endpoint==ep,]; CC <- matrix(0,nrow=nrow(z),ncol=length(coef(fit)),dimnames=list(NULL,names(coef(fit))))
  CC[,zn] <- as.matrix(z[,zn,drop=FALSE])
  if(ep=='joint') {
   w <- Wald_test(fit,constraints=CC,vcov=V,test='HTZ')
   rr <- data.frame(endpoint=ep,estimate=NA,se=NA,df=as.numeric(w$df_denom),low=NA,high=NA,p=as.numeric(w$p_val))
  } else {
   w <- linear_contrast(fit,vcov=V,contrasts=CC,test='Satterthwaite',p_values=TRUE)
   rr <- data.frame(endpoint=ep,estimate=w$Est,se=w$SE,df=w$df,low=w$CI_L,high=w$CI_U,p=w$p_val)
  }
  counter <- counter+1;results[[counter]] <- cbind(meta,rr)
 }
 cat('CR2',meta$id,'\n');flush.console()
 # Persist progress so an interrupted run has a readable checkpoint.
 write.csv(do.call(rbind,results),file.path(out,'cr2.csv'),row.names=FALSE)
}
# Panel unit-root tests using the package's tabulated Pesaran distributions.
panel <- read.csv(file.path(root,'data/processed/df_tcc_2013_2024.csv'),sep=';',fileEncoding='UTF-8-BOM')
panel$data_base <- as.Date(panel$data_base);panel <- panel[order(panel$uf,panel$data_base),]
stationarity <- list();j <- 0
for(per in c('Total','Pré')) {
 dat <- panel[panel$data_base<=as.Date(if(per=='Pré') '2020-01-01' else '2024-12-01'),]
 dat$delta <- ave(dat$taxa_inadimplencia,dat$uf,FUN=function(x)c(NA,diff(x)))
 for(series in c('taxa_inadimplencia','delta')) for(det in if(series=='delta') 'drift' else c('drift','trend')) for(lag in c(1,2)) {
  dd <- dat[!is.na(dat[[series]]),];pp <- pdata.frame(dd,index=c('uf','data_base'))
  test <- cipstest(pp[[series]],lags=lag,type=det,model='cmg',truncated=TRUE)
  j <- j+1;stationarity[[j]] <- data.frame(periodo=per,serie=series,deterministico=det,lags=lag,CIPS=as.numeric(test$statistic),p=as.numeric(test$p.value),N=27,T=length(unique(dd$data_base)))
 }
}
write.csv(do.call(rbind,stationarity),file.path(out,'cips.csv'),row.names=FALSE)
writeLines(capture.output(sessionInfo()),file.path(out,'r_session.txt'))
if(file.exists(file.path(cache,'cips_exposicoes_input.csv'))) {
 expo <- read.csv(file.path(cache,'cips_exposicoes_input.csv'));expo$data_base <- as.Date(expo$data_base)
 er <- list();j <- 0
 for(per in c('Total','Pré')) for(series in setdiff(names(expo),c('uf','data_base'))) for(lag in c(1,2)) {
  dd <- expo[expo$data_base<=as.Date(if(per=='Pré') '2020-01-01' else '2024-12-01'),]
  # Constant unit series undermine the individual CADF regressions. Do not drop UFs silently.
  constant <- any(tapply(dd[[series]],dd$uf,function(x) length(unique(x)))<3)
  j <- j+1
  if(constant) {er[[j]] <- data.frame(periodo=per,serie=series,lags=lag,CIPS=NA,p=NA,status='não calculável: UF com série constante ou quase constante')} else {
   pp <- pdata.frame(dd,index=c('uf','data_base'))
   test <- tryCatch(cipstest(pp[[series]],lags=lag,type='drift',model='cmg',truncated=TRUE),error=function(e) NULL)
   er[[j]] <- data.frame(periodo=per,serie=series,lags=lag,CIPS=if(is.null(test)) NA else as.numeric(test$statistic),p=if(is.null(test)) NA else as.numeric(test$p.value),status=if(is.null(test)) 'não calculável' else 'calculado')
  }
 }
 write.csv(do.call(rbind,er),file.path(out,'cips_exposicoes.csv'),row.names=FALSE)
}
