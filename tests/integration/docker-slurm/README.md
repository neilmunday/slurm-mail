# docker-slurm

This directory provides Docker images for various operating systems with a working Slurm installation. The images created from these Docker files are intended to allow tests to be performed against a Slurm version.

There are no persistent volumes so each invocation of the image creates a clean set-up.

## Naming

The images are named: `ghcr.io/neilmunday/slurm-mail/slurm-${OS_VERSION}`. E.g. `el9` for RHEL9 compatible operating systems.

## Building

Use the `SLURM_VER` build argument to specify the Slurm version to build in the image, e.g.

```
docker build --build-arg SLURM_VER=23.02.1 -f Dockerfile.el9 -t ghcr.io/neilmunday/slurm-mail/slurm-el9:23.02.1 -t ghcr.io/neilmunday/slurm-mail/slurm-el9:latest  .
```

**Note:** The first release of a Slurm version does not require `-1` in the `SLURM_VER` value.

## Running

### Environment Variables

The following environment variables can be set to control the behaviour of the container.

| Variable    | Default Value | Purpose                                                                                                     |
| ----------- | ------------- | ----------------------------------------------------------------------------------------------------------- |
| NODES       | `1`           | The total number of nodes in the cluster.                                                                   |
| NODE_PREFIX | `compute0`    | The prefix to use for node names.                                                                           |
| ROLE        | `HEAD`        | The role of the container: `HEAD` or `COMPUTE`. The head node will run `slurmctld`, `slurmdbd` and `mysql`. |

These variables can be used when running multiple instances of the container together.

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
