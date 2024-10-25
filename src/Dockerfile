## BUILD STAGE ##
FROM public.ecr.aws/lambda/python:3.12-arm64 AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN dnf install -y gcc g++ glibc-devel git

# clone optillm and comment out torch and transformers to greatly reduce image size
# Note: breaks cot_decoding and entropy_decoding
RUN git clone --depth 1 https://github.com/codelion/optillm.git /optillm && \
  rm -rf /optillm/.git /optillm/.github /optillm/*.png && \
  sed -i '/torch/d' /optillm/requirements.txt && \
  sed -i '/transformers/d' /optillm/requirements.txt

RUN pip install --no-cache-dir -r /optillm/requirements.txt

# Install optillm
RUN pip install --no-cache-dir /optillm

## RUNTIME STAGE ##
# Use the lambda Python ARM64 base image
FROM public.ecr.aws/lambda/python:3.12-arm64 AS runtime

# Copy installed site packages from the build stage
COPY --from=builder /var/lang/lib/python3.12/site-packages /var/lang/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy lambda function code
COPY ./api ./api
COPY requirements.txt .

# Install the function's dependencies
RUN pip3 install -r requirements.txt -U --no-cache-dir

# Set the CMD to your handler
CMD [ "api.app.handler" ]
