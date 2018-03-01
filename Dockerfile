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

RUN mkdir gcovr
COPY ./ gcovr/
RUN find gcovr -name *.pyc -delete
RUN source scl_source enable python27 devtoolset-6 && cd gcovr && pip install -e .
CMD source scl_source enable python27 devtoolset-6 && cd gcovr && python -m pytest -v
