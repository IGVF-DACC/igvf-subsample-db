# IGVF Subsample DB

This tool subsamples Postgres database of ENCODE/IGVF servers based on a subsampling rule JSON file.

## Subsampling rule JSON

This file defines subsampling rule(s) for each profile (e.g. `experiment` for ENCODE, `measurement_set` for IGVF). Multiple rules are allowed for each profile. Here is an example for ENCODE.
```json
{
    "file": [
        {
            "subsampling_min": 100,
            "subsampling_rate": 1e-03
        }
    ],
    "experiment": [
        {
            "subsampling_min": 3,
            "subsampling_rate": 1e-05,
            "subsampling_cond": {
                "assay_term_name": "ATAC-seq"
            }
        },
        {
            "subsampling_min": 5,
            "subsampling_rate": 1e-05,
            "subsampling_cond": {
                "assay_term_name": "ChIP-seq"
            }
        }
    ]
}
```

A rule is consist of `subsampling_min`, `subsampling_rate` and `subsampling_cond` (optional). See the following example of `experiment` profile of ENCODE.
```json
{
    "subsampling_min": 5,
    "subsampling_rate": 1e-05,
    "subsampling_cond": {
        "assay_term_name": "ChIP-seq"
    }
}
```

* `subsampling_min` defines the minimum number of objects in the profile after subsampling. It's bound to the actual number of objects. i.e. taking `MIN(number_of_objects, subsampling_min)`.
* `subsampling_rate` defines the minimum number of objects as total (respecting `subsampling_cond` if defined) number of objects in the profile multiplied by the rate. MAX of these two values will be taken as the final number of subsampled objects in the profile.
* `subsampling_cond` is a JSON object that defines conditions for the rule. For the above example, this will only subsample objects with a property `assay_term_name` defined as `ChIP-seq`. You can use any valid property in a profile. See profile's schema JSON to find such property.

There are currently 12548 `ChIP-seq` experiments and it will subsample 12548 objects down to `MAX(5, 1e-05*12548) = 5`.

For the case of `file` profile in the above example, there are currently 1458539 `file` objects on ENCODE. So it will subsample `1458539` objects down to `MAX(100, 1e-03 * 1458539) = 1458`.

You can have multiple rules under a single profile. See the case of `experiment` profile in the above example. It will include at least 3 `ATAC-Seq` experiments and 5 `ChIP-seq` experiments.

> **IMPORTANT**: Some users and their access_keys are important to run a server. Therefore, two examples keep **ALL** `user` and `access_key` for subsampling. i.e. `"subsampling_min": 1000000` is defined for `user` and `access_key`.


Examples keep **ALL** users after subsampling.


## Requirements

Install postgresql dev library on your system.

```bash
# apt
$ sudo apt-get install libpq-dev

# yum
$ sudo yum install postgresql-devel
```

## Running the tool with an RDS database (IGVF)

See this [document](docs/igvf.md) for details.


## Running the tool on a running demo (ENCODE)

See this [document](docs/encode.md) for details.
