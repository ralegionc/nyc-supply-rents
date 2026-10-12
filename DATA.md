# Data

This repository does not carry its raw inputs. The files listed below were present locally when the results in the README were produced, and were deleted on 2026-10-12 to reclaim **69.66 MB** of disk. Every one of them is a download from a public upstream source, so nothing unique was lost.

This file exists so that a re-download can be *checked* rather than assumed to match. It records the exact inventory, not just the source.

Upstream sources, with links and licences, are in the README under **Data**.

## What was removed

69.66 MB in 21 files.

| Path | Size | Files |
|---|---|---|
| `data/raw` | 69.66 MB | 21 |

## Restoring it

Re-run the fetch stage. `data/interim` was kept.

## Inventory

`data_manifest.csv` carries every file with its exact byte length and a fingerprint. Files of 32 MiB or less have a full `sha256`. Larger files have `headtail256`: a sha256 over the first mebibyte, the last mebibyte and the exact byte length, which catches a truncated or altered download without rereading gigabytes.

| File | Size | Fingerprint |
|---|---|---|
| `data/raw/zori_zip.csv` | 9.46 MB | `sha256:357c4544a4691608bbd20ff9941d4a112be54056fcae652de9d7cf41b601ac42` |
| `data/raw/housingdb_completions.json` | 7.79 MB | `sha256:08ef5510ae42fccf4e4a73a41ea4e40fd9e946e679ff1997a5f5acb2c6e17294` |
| `data/raw/pluto_bbl_0.json` | 3.06 MB | `sha256:e7dee9178f6ac16ebc1aa674c63a707fd6a7eeb1a3df0743eaee6beaf6ffd3e2` |
| `data/raw/pluto_bbl_1.json` | 3.05 MB | `sha256:91211cd6b6e62bd4f4bc69aad31c2b06650d6e1e0d75ac29cfa5c9340b2f1c85` |
| `data/raw/pluto_bbl_5.json` | 3.05 MB | `sha256:48a1cdb32d04811f71d5348c8c89fae6cdb50e9a54d8d57bf756a86838ea6b31` |
| `data/raw/pluto_bbl_3.json` | 3.05 MB | `sha256:3f5c33c6abd7503e58731bd0a809004e9c93d4686eca4df605de9d3ec51d2c0d` |
| `data/raw/pluto_bbl_6.json` | 3.05 MB | `sha256:5fde399099a25001a82d3c0723aabb14a6c1fd87574c51cd133dcca437c690d3` |
| `data/raw/pluto_bbl_8.json` | 3.05 MB | `sha256:84c95efd865db02ea9cbfd2d3a90492bcccc9f5d0ec57499affc8319f8836fe8` |
| `data/raw/pluto_bbl_12.json` | 3.05 MB | `sha256:316ba362bdf3219a001b1d9eceb49b87650faf6286314e4c5fd24a94b42577d0` |
| `data/raw/pluto_bbl_9.json` | 3.05 MB | `sha256:459ef9c4e9f2906570ee061bffcbe1ef6ebe0324b5b13257be38001c961ba0f2` |
| `data/raw/pluto_bbl_13.json` | 3.05 MB | `sha256:c2709143d1f6003614b07b61789ca13981ddf5bbfa3d647d5f4e0754e7bae016` |
| `data/raw/pluto_bbl_11.json` | 3.05 MB | `sha256:4d6a2f7daeeb9004b98756e8162fa03a2f4a44b03830e907efc7d03472ce7d0c` |
| `data/raw/pluto_bbl_7.json` | 3.05 MB | `sha256:b131ccce088c6ddc9139ce3584945a433287fae91c9d3b7108e3524cdf739192` |
| `data/raw/pluto_bbl_15.json` | 3.05 MB | `sha256:794f6a28f2597b3c4be7f5a76c75fada741caa0886af44b13f80be7d0de33557` |
| `data/raw/pluto_bbl_16.json` | 3.05 MB | `sha256:dc0e3036852067e3d534db56a7437eee43f1fd8f673464caa2f9868e51852670` |
| `data/raw/pluto_bbl_4.json` | 3.05 MB | `sha256:f442755bda5b781caf0839251a756958ab9b30336eaa239c7a9a07956293b58c` |
| `data/raw/pluto_bbl_10.json` | 3.05 MB | `sha256:e1834b6dd60a0dbabaf40441d1eff4e5c1ea65da8266c2e5c13e624e63a87130` |
| `data/raw/pluto_bbl_2.json` | 3.05 MB | `sha256:72ce99a3b8b375bf55da8071b67c94b60a308a9d885f7cfd633cb6c7a68d7087` |
| `data/raw/pluto_bbl_14.json` | 3.05 MB | `sha256:a187c2226365318d51427c8bd579ead2dad7dd3c5149a1f2bb2dbb686c32eae1` |
| `data/raw/pluto_bbl_17.json` | 536.95 KB | `sha256:ef89b88f338f1cccc7bb85e9ffcbabbab4ae46e57328c61dd42c33087e024d61` |
| `data/raw/manifest.json` | 6.50 KB | `sha256:a34d0668d4592bee7a4e79b4d6d6c80788487ccd79783883c7aaa7cb50734d8b` |

A source that is live rather than a fixed release will not reproduce these fingerprints. Where that applies it is said above.

