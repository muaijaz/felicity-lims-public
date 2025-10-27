# Docker Bake configuration for optimized Apple Silicon builds
# Usage: docker buildx bake -f docker-bake.hcl --load

variable "TAG" {
  default = "latest"
}

variable "REGISTRY" {
  default = ""
}

group "default" {
  targets = ["webapp", "webapi"]
}

target "webapp" {
  context    = "."
  dockerfile = "Dockerfile.dev"
  target     = "webapp"
  tags       = ["${REGISTRY}felicity-webapp:${TAG}"]
  platforms  = ["linux/arm64"]
  cache-from = ["type=local,src=/tmp/.buildx-cache"]
  cache-to   = ["type=local,dest=/tmp/.buildx-cache-new,mode=max"]
  output     = ["type=docker"]
}

target "webapi" {
  context    = "."
  dockerfile = "Dockerfile.dev"
  target     = "webapi"
  tags       = ["${REGISTRY}felicity-api:${TAG}"]
  platforms  = ["linux/arm64"]
  cache-from = ["type=local,src=/tmp/.buildx-cache"]
  cache-to   = ["type=local,dest=/tmp/.buildx-cache-new,mode=max"]
  output     = ["type=docker"]
}

# Multi-platform build target (for CI/CD)
target "multiplatform" {
  inherits = ["webapp", "webapi"]
  platforms = ["linux/amd64", "linux/arm64"]
}
