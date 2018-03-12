From centos:7
MAINTAINER JamesReynolds

ENV CONFIGURE_OPTS --disable-install-doc

ENV container docker
RUN yum install -y deltarpm
RUN yum upgrade -y
RUN yum install -y git centos-release-scl

RUN yum install -y devtoolset-6 cmake

RUN yum install -y python27-python-pip 

RUN source scl_source enable python27 devtoolset-6 && pip install pytest pyutilib

RUN yum install -y epel-release
RUN yum install -y python34-setuptools
RUN easy_install-3.4 pip
RUN pip install pytest pyutilib flake8


RUN mkdir gcovr
COPY ./ gcovr/
RUN source scl_source enable python27 devtoolset-6 && cd gcovr && pip install --upgrade pip setuptools && pip install -e .
RUN cd gcovr && pip install --upgrade pip setuptools && pip install -e .

CMD cd gcovr && flake8 --ignore=E501 && source scl_source enable devtoolset-6 && python3.4 -m pytest -v -x && source scl_source enable python27 && python -m pytest -v -x
