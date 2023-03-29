# docker-slurm

This directory provides Docker images for various operating systems with a working Slurm installation. The images created from these Docker files are intended to allow tests to be performed against a Slurm version.

At present there are no persistent volumes so each invocation of the image creates a clean set-up.

## Naming

The images are name: `ghcr.io/neilmunday/slurm-mail/slurm-${OS_VERSION}`. E.g. `el9` for RHEL9 compatible operating systems.

## Building

Use the `SLURM_VER` build argument to specify the Slurm version to build in the image, e.g.

```
docker build --build-arg SLURM_VER=23.02.1 -f Dockerfile.el9 -t ghcr.io/neilmunday/slurm-mail/slurm-el9:23.02.1 -t ghcr.io/neilmunday/slurm-mail/slurm-el9:latest  .
```

The default value is currently 23.02.1.

**Note:** The first release of a Slurm version does not require `-1` in the `SLURM_VER` value.

## Running

### Interactive

Run a container in interactive mode:

```
docker run -it --name slurm ghcr.io/neilmunday/slurm-mail/slurm-el9 /bin/bash
```

### Detached

Run the container in detached mode:

```
docker run -d --name slurm ghcr.io/neilmunday/slurm-mail/slurm-el9
```

Check that the container started ok:

```
docker logs slurm
```

Then you can run commands inside the container like so:

```
docker exec slurm sinfo
```

To submit a job:

```
docker exec -i slurm sbatch < myjob.sh
```
