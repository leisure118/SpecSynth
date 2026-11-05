ARG BASE_IMAGE=debian:bookworm-slim
FROM ${BASE_IMAGE}
ARG VERIFAST_VERSION=26.10
ARG VERIFAST_SHA256=5ad2a65997457fd5996a27f93107ef7e52c90c0d12b63b6e67f7acbc73e90efd
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl libgmp10 libgomp1 libstdc++6 && rm -rf /var/lib/apt/lists/*
RUN curl -fL --retry 3 "https://github.com/verifast/verifast/releases/download/${VERIFAST_VERSION}/verifast-${VERIFAST_VERSION}-linux.tar.gz" -o /tmp/verifast.tar.gz \
    && echo "${VERIFAST_SHA256}  /tmp/verifast.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/verifast.tar.gz -C /opt && rm /tmp/verifast.tar.gz
ENV PATH="/opt/verifast-26.10/bin:${PATH}"
WORKDIR /work
CMD ["verifast", "-help"]
