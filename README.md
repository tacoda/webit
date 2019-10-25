# WebIt

WebIt is a tool that will sync a local directory to an s3 bucket
and optionally configure Route 23 and CloudFront as well.

## Features

WebIt currently has the following features:

- List buckets
- List contents of a bucket
- Create and set up bucket
- Sync directory tree to bucket
- Set AWS profile with `--profile=<profileName>`
- Configure a Route 53 domain

## Installation

```sh
pip3 install https://s3.amazonaws.com/tacoda-dist/webit/WebIt-0.1-py3-none-any.whl
```
