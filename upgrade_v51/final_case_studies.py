"""Generate the restricted examples for the completed aggregate-proposer run."""
import common
common.PRIVATE = common.PRIVATE / "cloud"
import case_studies
if __name__ == "__main__":
    case_studies.main()
