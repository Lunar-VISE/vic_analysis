from vic_analysis.radiance_pipeline.data_model import VICDataset


class Step:
    def __init__(self, name: str, enabled: bool = True, save: bool = True) -> None:
        self.name = name
        self.enabled = enabled
        self.save = save
        self.is_active: bool = False

    def run(self, dset: VICDataset) -> VICDataset:
        raise NotImplementedError("Subclasses must implement run()")

    def execute(self, data: VICDataset) -> VICDataset:
        if not self.enabled:
            return data
        return self.run(data)
