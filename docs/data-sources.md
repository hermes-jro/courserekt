# Data provenance

## AY2026/2027 Semester 1 — Round 2 vacancy

Retrieved at **2026-07-28 09:08:46 SGT** directly from the official NUS CourseReg endpoint, using `https://www.nus.edu.sg/coursereg/` as the HTTP referer and a normal browser user agent. The server filename was `VacancyRpt_R2.pdf`; the final response was HTTP 200 with `Content-Type: application/pdf`, `Content-Length: 991329`, no redirects, and effective URL `https://www.nus.edu.sg/coursereg/docs/VacancyRpt_R2.pdf`.

The source first appeared in live Discord history in guild `1524704629558870127`, parent channel `nus-general` (`1524709642863902741`), thread `R2 Allocation Report Scheduled Fetch` (`1531463906919186514`). Hermes (`1524705469199810570`) posted the official-link message `1531467640722428095` at 2026-07-28 09:05:38 SGT and the attachment message `1531467647999414293` at 09:05:40 SGT with filename `VacancyRpt_R2_20260728_090358.pdf`. The Discord attachment and fresh official download were byte-identical.

| Repository path | Official durable source | SHA-256 | Pages | Report date |
| --- | --- | --- | ---: | --- |
| `src/history/vacancy_history/data/pdfs/2627/1/round_2.pdf` | `https://www.nus.edu.sg/coursereg/docs/VacancyRpt_R2.pdf` | `40fb6145167103ee8e4afad9cd6ec6745a858791460b5136686e248b0f9e2ee7` | 252 | As at 27-Jul-26; updated 27/07/2026 |

The file starts with `%PDF-1.6`, ends with a PDF EOF marker, and identifies its producer as Oracle Analytics Publisher. Strict parsing extracted 1,542,524 characters from all 252 pages with no empty pages: every page identifies `Course Class Vacancy Report`, `Semester 1, AY2026/2027`, and `As at 27-Jul-26`, while page 1 also states `updated: 27/07/2026`.

`qpdf --check` found no syntax or stream-encoding errors. The repository active-content audit, run as an unprivileged user in a read-only, network-disabled container, found no embedded files, JavaScript, launch/open actions, external URIs, XFA, rich media, or other active content. The PDF uses AESv2 permissions but opens with an empty password and was completely parsed without executing embedded content.

Only the official Round 2 **vacancy** report is included. No undergraduate or graduate Round 2 demand/allocation PDF has been added while those official reports remain unavailable.

## AY2026/2027 Semester 1 — Round 1

Retrieved on 23 July 2026 from the official [NUS CourseReg Resources](https://www.nus.edu.sg/coursereg/resources.html) page after NUS announced that Round 1 results and demand/allocation reports were available.

| Repository path | Official source | SHA-256 | Pages |
| --- | --- | --- | ---: |
| `src/history/vacancy_history/data/pdfs/2627/1/round_1.pdf` | `https://www.nus.edu.sg/coursereg/docs/VacancyRpt_R1.pdf` | `fa2cef5c2a3296b2f30e12c5a68ad269b82cfa2efe68fa68ace86c64d2fce73b` | 252 |
| `src/history/coursereg_history/data/pdfs/2627/1/ug/round_1.pdf` | `https://www.nus.edu.sg/coursereg/docs/DemandAllocationRptUG_R1.pdf` | `794513b095ea474e59f51177cd48924e05da69083ccc65be32bd6880f1616769` | 103 |
| `src/history/coursereg_history/data/pdfs/2627/1/gd/round_1.pdf` | `https://www.nus.edu.sg/coursereg/docs/DemandAllocationRptGD_R1.pdf` | `9af8b154dfb4d2950e763efdac3846c9913022fc86247faac6f60ff669b4f60c` | 62 |

The first-page text of each demand/allocation report identifies it as Semester 1, AY2026/2027, Select Courses Round 1. Before inclusion, all three PDFs passed `qpdf --check` and an isolated, network-disabled structural scan found no embedded files, JavaScript, launch/open actions, external URIs, XFA, rich media, or other active PDF content.
