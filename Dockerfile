FROM jenkinsxio/builder-base:latest

RUN yum update -y \
    && yum install -y https://centos7.iuscommunity.org/ius-release.rpm \
    && yum install -y python36u python36u-libs python36u-devel python36u-pip \
    && yum install -y which gcc \ 
    && yum install -y openldap-devel 

COPY . /srv/service/monoci
WORKDIR /srv/service

RUN pip3.6 install --upgrade pip && \
    pip3.6 install -e monoci

CMD ["helm" "version"]