from src.workflows.base import BaseWorkflow, WorkflowDefinition


class TempatPelayananKbWorkflow(BaseWorkflow):
    definition = WorkflowDefinition(
        key="yankb_pelkon.tempat_pelayanan_kb",
        name="Tempat Pelayanan KB",
        route="/pendaftaran",
        strategy="browser_or_api",
        required_fields=[
            "nama_tempat_pelayanan",
            "kode_faskes",
            "provinsi",
            "kabupaten",
            "kecamatan",
        ],
        risk="medium",
    )


WORKFLOW_REGISTRY: dict[str, type[BaseWorkflow]] = {
    TempatPelayananKbWorkflow.definition.key: TempatPelayananKbWorkflow,
}


def get_workflow(target_key: str) -> BaseWorkflow:
    if target_key not in WORKFLOW_REGISTRY:
        raise KeyError(f"Workflow belum tersedia untuk target: {target_key}")
    return WORKFLOW_REGISTRY[target_key]()
