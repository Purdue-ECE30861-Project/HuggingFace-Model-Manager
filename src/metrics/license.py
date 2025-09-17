from metric import BaseMetric
from typing import Self, override

license_score: dict[str, float] = {
    # 0.0 means either non-commercial or incompatible with LGPL v2.1 (see https://www.gnu.org/licenses/license-list.html)
    "apache-2.0": 0.0, # only compatible with gpl v3
    "mit": 1.0,
    # all incompatible because they impose restrictions on reuse not present in the LGPL
    "openrail": 0.0,
    "creativeml-openrail-m": 0.0,
    "bigscience-openrail-m": 0.0,
    "bigscience-bloom-rail-1.0": 0.0,
    "bigcode-openrail-m": 0.0,

    "afl-3.0": 0.0,
    "artistic-2.0": 0.9,
    "bsl-1.0": 1.0,
    "bsd": 1.0,
    "bsd-2-clause": 1.0,
    "bsd-3-clause": 1.0,
    "bsd-3-clause-clear": 1.0,
    "c-uda": 0.5, # a bit of an odd-ball, hard to know for sure
    # cc is too broad since it could include sharealike and non-commercial licenses; use fallback
    "cc0-1.0": 1.0,
    "cc-by-2.0": 1.0,
    "cc-by-2.5": 1.0,
    "cc-by-3.0": 1.0,
    "cc-by-4.0": 1.0,
    "cc-by-sa-3.0": 0.0,
    "cc-by-sa-4.0": 0.0,
    "cc-by-nc-2.0": 0.0,
    "cc-by-nc-3.0": 0.0,
    "cc-by-nc-4.0": 0.0,
    "cc-by-nc-nd-3.0": 0.0,
    "cc-by-nc-nd-4.0": 0.0,
    "cc-by-nc-sa-2.0": 0.0,
    "cc-by-nc-sa-3.0": 0.0,
    "cc-by-nc-sa-4.0": 0.0,
    "cdla-sharing-1.0": 0.0,
    "cdla-permissive-1.0": 1.0,
    "cdla-permissive-2.0": 1.0,

    "wtfpl": 1.0,
    "ecl-2.0": 0.0, # only compatible with gpl v3.0 
    "epl-1.0": 0.0,
    "epl-2.0": 0.3, # potentially usable depending on the secondary license allowances
    "etalab-2.0": 0.0,

    # technically compatible through crazy relicensing shenanigans
    "eupl-1.1": 0.3,
    "eupl-1.2": 0.3,

    "agpl-3.0": 0.0,
    "gfdl": 0.0, # for documentation, so likely weird compatibility-wise
    "gpl": 1.0, # lgpl says you can choose whatever gpl license you want if it isn't specified by the distributor

    # remember all code is distributed under LGPL v2.1
    # see https://www.gnu.org/licenses/gpl-faq.html#AllCompatibility
    "gpl-2.0": 0,
    "gpl-3.0": 0.0,
    "lgpl": 1.0, #  lgpl says you can choose whatever lgpl license you want if it isn't specified by the distributor
    "lgpl-2.1": 1.0,
    "lgpl-3.0": 0.7, # re-use is allowed, but modification will require the code to be relicensed.
    
    "isc": 1.0,
    "h-research": 0.0, # non commercial
    "intel-research": 0.0, # restrictions on redistribution.
    "lppl-1.3c": 0.0, # incompatible with gpl v2/3, unsure with lgpl, also no real models use it.
    "ms-pl": 0.0, # copyleft and incompatible with gpl copyleft
    "apple-ascl": 0.5, # can redistribute as long as no modifications are made
    "apple-amlr": 0.0, # can only use for research purposes
    "mpl-2.0": 1.0,
    "odc-by": 1.0,
    "odbl": 0.0,
    "openmdw-1.0": 1.0,
    "openrail++": 0.0,
    "osl-3.0": 0.0,
    "postgresql": 1.0,
    "ofl-1.1": 0.0, # copyleft
    "ncsa": 1.0,
    "unlicense": 1.0,
    "zlib": 1.0,
    "pddl": 1.0,
    "lgpl-lr": 1.0,
    "deepfloyd-if-license": 0.0, # non-commercial
    "fair-noncommercial-research-license": 0.0,

    # all the llama licenses are not free software licenses, so they can't be
    # redistributed under the LGPL
    "llama2": 0.0,
    "llama3": 0.0,
    "llama3.1": 0.0,
    "llama3.2": 0.0,
    "llama3.3": 0.0,
    "llama4": 0.0,

    # can't redistribute under LGPL, not an open source license
    "gemma": 0.0
}

class LicenseMetric(BaseMetric):

    def __init__(self):
        """
        Initializes the BaseMetric with default values.
        """
        self.score: float = 0.0
        self.metric_name = "license"
        self.url: str = ""
        self.priority: int = 1
        self.target_platform: str = ""

    @override
    def run(self) -> Self:
        ...


