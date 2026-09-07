# deployctl
A zero-touch deployment command-line interface (CLI) tool.

## Sources
- [Installing Docker Engine](https://docs.docker.com/engine/)
- [Nginx via Python](https://pypi.org/project/nginx-python/)

## Modules (To-Do)
- [x] lint (unit test)
- [x] docker (build + scan)
- [ ] deploy (ssh connection) + health check
  - [x] deployment via nginx reverse proxying
  - [ ] deployment via linux screen
- [ ] rollback
- [ ] logging?
  - [ ] mysql logging
  - [ ] flat file?
> [!TIP]
> figure out how to get this integrated to other projects -> homebrew? etc or dockerize it