# deployctl
A zero-touch deployment command-line interface (CLI) tool.

## Sources
- [Installing Docker Engine](https://docs.docker.com/engine/)

## Modules (To-Do)
- [x] lint (unit test)
- [x] docker (build + scan)
- [x] deploy (ssh connection)
  - [x] deployment via nginx reverse proxying
  - [x] deployment via linux screen
- [x] joining of everything
- [x] health check (curl the app port on the VPS after a deploy)
- [x] rollback (docker: previous image tag, linux: previous synced directory): auto-triggered on a failed health check
- [ ] logging?
  - [ ] mysql logging
  - [ ] flat file?
> [!TIP]
> figure out how to get this integrated to other projects -> homebrew? etc or dockerize it — dockerized: see Dockerfile, published to GHCR via CI