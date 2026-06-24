from meshwork.automation.workflow import Node, Workflow


def test_workflow_instances_do_not_share_mutable_state() -> None:
    first = Workflow()
    second = Workflow()

    first.nodes["a"] = Node(id="a", type="source", data={})

    assert second.nodes == {}


def test_workflow_nodes_do_not_share_relationship_lists() -> None:
    parent = Node(id="parent", type="source", data={})
    child = Node(id="child", type="sink", data={})
    sibling = Node(id="sibling", type="sink", data={})

    child.parents.append(parent)

    assert sibling.parents == []
