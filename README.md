# PiCN Routing Performance Measurement

A small collection of performance tests for routing in [s3lph/picn][s3lph-picn].

## Usage

### With Docker

```sh
mkdir raw
mkdir plots
docker build .
docker run -d -v $(realpath raw):/raw -v $(realpath plots):/plots <image id>
```

### Without Docker

Dependencies:

  - git
  - Python >= 3.6
  - pip
  - Matplotlib

```sh
./setup.sh
./run.sh
```

## Results

The files produced by each run are tagged with the UNIX timestamp of the start of
the run (in UTC) to avoid overwriting results from previous runs.  For each test
case, a CSV file is created in `raw/`.  The raw data is of the form

```csv
param1,param2,...,paramN,time,result
```

where `param1` to `paramN` are testcase-specific parameters (see below), `time`
is the time in seconds the run took to complete.  `result` is `ok` if the test
run completed successfully, and `fail` otherwise.

Plots generated from the raw CSV data are placed in `plots/`.  The filenames
contain the timestamp, the name of the test case, and the parameters that
remain constant in the plot.

## Test Cases

### `depth`

#### Test Setup

!["depth" test case setup](img/depth.png)

#### Parameters

1. `n` - The number of forwarders between client and repo
2. `interval` - The routing information exchange interval, in seconds

#### Plots

For each routing interval  in `0.5, 1.0, 2.0`, there is one plot describing the
time until the client was able to fetch data from the repo, depending on the
number of forwarders in between.

### `breadth`

#### Test Setup

!["breadth" test case setup](img/breadth.png)

#### Parameters

1. `n` - The number of forwarders in the middle layer
2. `interval` - The routing information exchange interval, in seconds

#### Plots

For each routing interval  in `0.5, 1.0, 2.0`, there is one plot describing the
time until the client was able to fetch data from the repo, depending on the
number of forwarders in the middle layer.

### `depth_rand`

Like `depth`, but with randomized starting order of forwarders and a small
randomzied delay between starting the forwarders.

### `breadth_rand`

Like `breadth`, but with randomized starting order of forwarders and a small
randomzied delay between starting the forwarders.

[s3lph-picn]: https://github.com/s3lph/picn
