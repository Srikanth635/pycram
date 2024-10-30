from dataclasses import dataclass
from __future__ import annotations
from typing_extensions import Iterable, Optional, Callable, Dict, Any, List, Union, Tuple
from pycram.worlds.bullet_world import World, Object
import os

@dataclass
class OwlPrefixName:
    prefix : str
    local_name: str

@dataclass
class OwlAttributeValue:
    namespace : str
    local_value: str

@dataclass
class OwlAttribute:
    key : OwlPrefixName
    value : OwlAttributeValue

@dataclass
class OwlEntityDTD:
    entity_pairs : List[Tuple(str, str )]
    name: OwlPrefixName = OwlPrefixName("rdf", "RDF")

@dataclass
class OwlNode:
    name : OwlPrefixName
    value : str
    attributes : List[OwlAttribute]
    child_nodes : List[OwlNode]
    comment : str

    def add_child_node(self, child_node: OwlNode):
        self.child_nodes.append(child_node)

    def add_child_nodes(self, child_nodes: List[OwlNode]):
        self.child_nodes.extend(child_nodes)

    def add_attribute(self, attribute: OwlAttribute):
        self.attributes.append(attribute)

    def add_attributes(self, attributes: List[OwlAttribute]):
        self.attributes.extend(attributes)

    def set_comment(self, comment: str):
        self.comment = comment

    def create_resource_property(self, namespace : str, value : str) -> OwlNode:
        rdf_resource : OwlPrefixName = OwlPrefixName("rdf", "RDF")
        rdf_type : OwlPrefixName = OwlPrefixName("rdf", "type")
        return OwlNode(rdf_type, OwlAttribute(rdf_resource, OwlAttributeValue(namespace, value)))

@dataclass
class OwlCommentNode(OwlNode):
    comment : str

@dataclass
class SemanticMapWriterParams:
    template : str
    directory_path : str
    id : str
    description : str
    level : str
    overwrite : bool

@dataclass
class OwlDoc:
    entity_definitions : List[OwlEntityDTD]
    namespaces : List[OwlAttribute]
    ontology_imports : OwlNode
    property_definitions : List[OwlNode]
    datatype_definitions : List[OwlNode]
    class_definitions : List[OwlNode]
    individuals : List[OwlNode]
    prefix : str
    ontology_name : str
    id : str

    def add_entity_definition_pair(self, inEntityDefinition : Tuple(str,str)):
        self.entity_definitions.append(inEntityDefinition)

    def add_entity_definition_strings(self, inKey : str, inVal: str):
        self.entity_definitions.append(Tuple(inKey,inVal))

    def add_entity_definitions_list(self, inEntityDefinitions : List[Tuple(str,str)]):
        self.entity_definitions.extend(inEntityDefinitions)

    def add_namespace_declaration(self, inAttribute : OwlAttribute):
        self.namespaces.append(inAttribute)

    def add_namespace_declaration_string(self, inPrefix : OwlPrefixName , inAttributeValue : OwlAttributeValue):
        self.add_namespace_declaration(OwlAttribute(inPrefix, inAttributeValue))

    def add_namespace_declaration_strings(self, inPrefix : str , inPrefixName : str, inAttributeValue : str):
        self.add_namespace_declaration(OwlPrefixName(inPrefix,inPrefixName),OwlAttributeValue(inAttributeValue))

    def add_namespace_declarations_list(self, inAttributes : List[OwlAttribute]):
        self.namespaces.extend(inAttributes)

    def create_ontology_node(self):
        rdf_about : OwlPrefixName = OwlPrefixName("rdf", "about")
        owl_ontology : OwlPrefixName = OwlPrefixName("owl", "Ontology")

        self.ontology_imports.name = owl_ontology
        self.ontology_imports.add_attribute(OwlAttribute(rdf_about, OwlAttributeValue("http://knowrob.org/kb/" +
                                                                                      self.ontology_name + ".owl")))
        self.ontology_imports.comment = "Ontologies"

    def add_ontology_import(self, imports : str):
        owl_imports = OwlPrefixName("owl", "imports")
        rdf_resource = OwlPrefixName("rdf", "resource")

        self.ontology_imports.add_child_node(OwlNode(owl_imports,OwlAttribute(rdf_resource,OwlAttributeValue(imports))))

    def add_property_definition(self, inNs : str, inName : str):
        rdf_about = OwlPrefixName("rdf", "about")
        owl_op = OwlPrefixName("owl", "ObjectProperty")
        self.add_property_definitions(OwlNode(owl_op,OwlAttribute(rdf_about, OwlAttributeValue(inNs,inName))))

    def add_property_definitions(self, inNode : OwlNode):
        self.property_definitions.append(inNode)

    def add_datatype_definition(self, inNs : str, inName : str):
        rdf_about = OwlPrefixName("rdf", "about")
        owl_dp = OwlPrefixName("owl", "DatatypeProperty")
        self.add_datatype_definitions(OwlNode(owl_dp, OwlAttribute(rdf_about, OwlAttributeValue(inNs,inName))))

    def add_datatype_definitions(self, inNode : OwlNode):
        self.datatype_definitions.append(inNode)

    def add_class_definition(self, inNs : str, inName : str):
        self.add_class_definitions(OwlAttributeValue(inNs,inName))

    def add_class_definitions(self, av : OwlAttributeValue):
        rdf_about = OwlPrefixName("rdf", "about")
        owl_cls = OwlPrefixName("owl", "Class")
        self.add_class_definitions_(OwlNode(owl_cls,OwlAttribute(rdf_about, av)))

    def add_class_definitions_(self, inNode : OwlNode):
        self.class_definitions.append(inNode)

    def add_individual(self, inChildNode : OwlNode):
        self.individuals.append(inChildNode)

    def add_individuals(self, inChildNodes : List[OwlNode]):
        self.individuals.extend(inChildNodes)

    def print_to_string(self):
        indent = ""
        docstr = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n\n"
        docstr += str(self.entity_definitions)
        root = OwlNode(OwlPrefixName("rdf", "RDF"), self.namespaces)
        root.add_child_node(self.ontology_imports)
        root.add_child_nodes(self.property_definitions)
        root.add_child_nodes(self.datatype_definitions)
        root.add_child_nodes(self.class_definitions)
        root.add_child_nodes(self.individuals)
        docstr += str(root)
        print(docstr)
        return docstr

@dataclass
class OwlSemanticMap(OwlDoc):
    sem_map_individual : OwlNode

    def add_semantic_map_individual(self, indescription : str, inlevelname : str):
        owl_ni = OwlPrefixName("owl", "NamedIndividual")
        rdf_about = OwlPrefixName("rdf", "about")
        rdf_type = OwlPrefixName("rdf", "type")
        rdf_resource = OwlPrefixName("rdf", "resource")
        kb_map_description = OwlPrefixName("knowrob", "mapDescription")
        kb_level_name = OwlPrefixName("knowrob", "levelName")
        rdf_datatype = OwlPrefixName("rdf", "datatype")
        attr_val_string = OwlAttributeValue("xsd", "string")
        sem_map_id = OwlAttributeValue(self.prefix, self.id)

        self.sem_map_individual.name = owl_ni
        self.sem_map_individual.add_attribute((OwlAttribute(rdf_about, sem_map_id)))
        self.sem_map_individual.add_child_node(OwlNode(rdf_type, OwlAttribute(rdf_resource,
                                                            OwlAttributeValue("knowrob", "SemanticEnvironmentMap"))))
        self.sem_map_individual.add_child_node(OwlNode(kb_map_description,
                                                       OwlAttribute(rdf_datatype,attr_val_string),indescription))
        self.sem_map_individual.add_child_node(OwlNode(kb_level_name,
                                                       OwlAttribute(rdf_datatype,attr_val_string), inlevelname))
        self.sem_map_individual.comment = "Semantic Map" + self.id

        self.individuals.append(self.sem_map_individual)

@dataclass
class OwlSemanticMapStatics:
    @staticmethod
    def create_default_semantic_map(inSemMapId: str, inDocPrefix: str, inDocOntologyName: str) -> OwlSemanticMap:
        sem_map : OwlSemanticMap = OwlSemanticMap(inDocPrefix, inDocOntologyName, inSemMapId)

        # Adding definitions
        sem_map.add_entity_definition_strings("owl", "http://www.w3.org/2002/07/owl#")
        sem_map.add_entity_definition_strings("xsd", "http://www.w3.org/2001/XMLSchema#")
        sem_map.add_entity_definition_strings("knowrob", "http://knowrob.org/kb/knowrob.owl#")
        sem_map.add_entity_definition_strings("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
        sem_map.add_entity_definition_strings("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        sem_map.add_entity_definition_strings("log", "http://knowrob.org/kb/ameva_log.owl#")

        # Adding namespaces
        sem_map.add_namespace_declaration_strings("xmlns", "", "http://knowrob.org/kb/ameva_log.owl#")
        sem_map.add_namespace_declaration_strings("xml", "base", "http://knowrob.org/kb/ameva_log.owl#")
        sem_map.add_namespace_declaration_strings("xmlns", "owl", "http://www.w3.org/2002/07/owl#")
        sem_map.add_namespace_declaration_strings("xmlns", "xsd", "http://www.w3.org/2001/XMLSchema#")
        sem_map.add_namespace_declaration_strings("xmlns", "knowrob", "http://knowrob.org/kb/knowrob.owl#")
        sem_map.add_namespace_declaration_strings("xmlns", "rdfs", "http://www.w3.org/2000/01/rdf-schema#")
        sem_map.add_namespace_declaration_strings("xmlns", "rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        sem_map.add_namespace_declaration_strings("xmlns", "log", "http://knowrob.org/kb/ameva_log.owl#")

        # Adding imports
        sem_map.create_ontology_node()
        sem_map.add_ontology_import("package://knowrob/owl/knowrob.owl")

        # Adding property definitions
        sem_map.add_property_definitions(OwlCommentNode("Property Definitions"))
        sem_map.add_property_definition("knowrob", "describedInMap")
        sem_map.add_property_definition("knowrob", "pathToCadModel")
        sem_map.add_property_definition("knowrob", "overlapEvents")
        sem_map.add_property_definition("knowrob", "mobility")
        sem_map.add_property_definition("knowrob", "levelName")
        sem_map.add_property_definition("knowrob", "tagsData")
        sem_map.add_property_definition("knowrob", "gravity")
        sem_map.add_property_definition("knowrob", "mapDescription")

        # Adding datatype definitions
        sem_map.add_datatype_definitions(OwlCommentNode("Datatype Definitions"))
        sem_map.add_datatype_definition("knowrob", "quaternion")
        sem_map.add_datatype_definition("knowrob", "translation")

        # Adding class definitions
        sem_map.add_class_definitions_(OwlCommentNode("Class Definitions"))
        sem_map.add_class_definition("knowrob", "SemanticEnvironmentMap")
        sem_map.add_class_definition("knowrob", "Pose")

        return sem_map

    @staticmethod
    def create_object_individual(inDocPrefix: str, inId: str, class_ : str) -> OwlNode:
        rdf_about = OwlPrefixName("rdf", "about")
        owl_ni = OwlPrefixName("owl", "NamedIndividual")

        object_individual = OwlNode(owl_ni, OwlAttribute(rdf_about, OwlAttributeValue(inDocPrefix,inId)))
        object_individual.comment = "Individual " + class_ + "/* " + inId + "*/"
        object_individual.add_child_node(OwlSemanticMapStatics.create_class_property(class_))
        return object_individual

    @staticmethod
    def create_pose_individual(inDocPrefix: str, inId: str, inLoc, inQaut) -> OwlNode:
        rdf_about = OwlPrefixName("rdf", "about")
        rdf_type = OwlPrefixName("rdf", "type")
        rdf_resource = OwlPrefixName("rdf", "resource")
        owl_ni = OwlPrefixName("owl", "NamedIndividual")
        attr_val_pose = OwlAttributeValue("knowrob","Pose")

        pose_individual = OwlNode(owl_ni,OwlAttribute(rdf_about, OwlAttributeValue(inDocPrefix,inId)))
        pose_property = OwlNode(rdf_type, OwlAttribute(rdf_resource, attr_val_pose))
        pose_individual.add_child_node(pose_property)
        pose_individual.add_child_node(OwlSemanticMapStatics.create_quaternion_property(inQaut))
        pose_individual.add_child_node(OwlSemanticMapStatics.create_location_property(inLoc))
        return pose_individual

    @staticmethod
    def create_constraint_individual(inDocPrefix: str, inId: str, parentId: str, childId: str) -> OwlNode:
        rdf_about = OwlPrefixName("rdf", "about")
        owl_ni = OwlPrefixName("owl", "NamedIndividual")
        object_individual = OwlNode(owl_ni, OwlAttribute(rdf_about, OwlAttributeValue(inDocPrefix,inId)))
        object_individual.comment = "Constraint/*" + inId + "*/"
        object_individual.add_child_node(OwlSemanticMapStatics.create_class_property("Constraint"))
        object_individual.add_child_node(OwlSemanticMapStatics.create_parent_property(inDocPrefix,parentId))
        object_individual.add_child_node(OwlSemanticMapStatics.create_child_property(inDocPrefix,childId))

        return object_individual

    @staticmethod
    def create_linear_constraint_properties(inDocPrefix: str, inId: str, xMotion: int, yMotion: int, zMotion: int,
                                            limit: float, soft_constraint: bool, stiffness: bool, damping: float):
        pass

    @staticmethod
    def create_angular_constraint_properties(inDocPrefix: str, inId: str, xMotion: int, yMotion: int, zMotion: int,
                                            limit: float, soft_constraint: bool, stiffness: bool, damping: float):
        pass

    @staticmethod
    def create_class_definition(class_: str) -> OwlNode:
        rdf_about = OwlPrefixName("rdf", "about")
        owl_class = OwlPrefixName("owl", "Class")

        return OwlNode(owl_class, OwlAttribute(rdf_about, OwlAttributeValue("knowrob",class_)))

    @staticmethod
    def create_generic_resource_property(inPrefix_name : OwlPrefixName, inAttributeValue : OwlAttributeValue) -> OwlNode:
        pass

    @staticmethod
    def create_class_property(class_ : str) -> OwlNode:
        rdf_resource = OwlPrefixName("rdf", "resource")
        rdf_type = OwlPrefixName("rdf", "type")

        return OwlNode(rdf_type, OwlAttribute(rdf_resource, OwlAttributeValue("knowrob",class_)))

    @staticmethod
    def create_described_in_map_property(inDocPrefix: str, inDocId: str) -> OwlNode:
        pass

    @staticmethod
    def create_path_to_cad_model_property(inPath: str):
        pass

    @staticmethod
    def create_tags_data_property():
        pass

    @staticmethod
    def create_sub_class_of_property(inSubClassOf : str) -> OwlNode:
        rdf_resource = OwlPrefixName("rdf", "resource")
        rdfs_subclass_of = OwlPrefixName("rdfs", "subClassOf")
        return OwlNode(rdfs_subclass_of, OwlAttribute(rdf_resource, OwlAttributeValue("knowrob",inSubClassOf)))

    @staticmethod
    def create_skeletal_bone_property():
        pass

    @staticmethod
    def create_depth_property(value: float) -> OwlNode:
        rdfs_subclass_of = OwlPrefixName("rdfs", "subClassOf")
        owl_restriction = OwlPrefixName("owl", "Restriction")
        owl_hasVal = OwlPrefixName("owl", "hasValue")

        subclass = OwlNode(rdfs_subclass_of)
        restriction = OwlNode(owl_restriction)
        restriction.add_child_node(OwlSemanticMapStatics.create_on_property("depthOfObject"))
        restriction.add_child_node(OwlSemanticMapStatics.create_float_value_property(owl_hasVal,value))
        subclass.add_child_node(restriction)

        return subclass

    @staticmethod
    def create_height_property(value: float):
        rdfs_subclass_of = OwlPrefixName("rdfs", "subClassOf")
        owl_restriction = OwlPrefixName("owl", "Restriction")
        owl_hasVal = OwlPrefixName("owl", "hasValue")

        subclass = OwlNode(rdfs_subclass_of)
        restriction = OwlNode(owl_restriction)
        restriction.add_child_node(OwlSemanticMapStatics.create_on_property("heightOfObject"))
        restriction.add_child_node(OwlSemanticMapStatics.create_float_value_property(owl_hasVal, value))
        subclass.add_child_node(restriction)

        return subclass

    @staticmethod
    def create_width_property(value: float):
        rdfs_subclass_of = OwlPrefixName("rdfs", "subClassOf")
        owl_restriction = OwlPrefixName("owl", "Restriction")
        owl_hasVal = OwlPrefixName("owl", "hasValue")

        subclass = OwlNode(rdfs_subclass_of)
        restriction = OwlNode(owl_restriction)
        restriction.add_child_node(OwlSemanticMapStatics.create_on_property("widthOfObject"))
        restriction.add_child_node(OwlSemanticMapStatics.create_float_value_property(owl_hasVal, value))
        subclass.add_child_node(restriction)

        return subclass

    @staticmethod
    def create_on_property(inProperty: str, Ns: str = "knowrob") -> OwlNode:
        owl_on_prop = OwlPrefixName("owl", "OnProperty")
        rdf_resource = OwlPrefixName("rdf", "resource")
        return OwlNode(owl_on_prop, OwlAttribute(rdf_resource, OwlAttributeValue(Ns,inProperty)))

    @staticmethod
    def create_bool_value_property(inPrefixName: OwlPrefixName, bValue : bool) -> OwlNode:
        rdf_datatype = OwlPrefixName("rdf", "datatype")
        attr_valBool = OwlAttributeValue("xsd","boolean")

        return OwlNode(inPrefixName,OwlAttribute(rdf_datatype,attr_valBool), str(bValue))

    @staticmethod
    def create_int_value_property(inPrefixName: OwlPrefixName, value : int) -> OwlNode:
        rdf_datatype = OwlPrefixName("rdf", "datatype")
        attr_valInt = OwlAttributeValue("xsd", "integer")

        return OwlNode(inPrefixName, OwlAttribute(rdf_datatype, attr_valInt), str(value))

    @staticmethod
    def create_float_value_property(inPrefixName: OwlPrefixName, value : float) -> OwlNode:
        rdf_datatype = OwlPrefixName("rdf", "datatype")
        attr_valfloat = OwlAttributeValue("xsd", "float")

        return OwlNode(inPrefixName, OwlAttribute(rdf_datatype, attr_valfloat), str(value))

    @staticmethod
    def create_string_value_property(inPrefixName: OwlPrefixName, inValue : str) -> OwlNode:
        rdf_datatype = OwlPrefixName("rdf", "datatype")
        attr_valString = OwlAttributeValue("xsd", "string")

        return OwlNode(inPrefixName, OwlAttribute(rdf_datatype, attr_valString), inValue)

    @staticmethod
    def create_pose_property(inDocPrefix: str, inId: str) -> OwlNode:
        kb_pose = OwlPrefixName("knowrob", "pose")
        rdf_resource = OwlPrefixName("rdf", "resource")
        return OwlNode(kb_pose, OwlAttribute(rdf_resource, OwlAttributeValue(inDocPrefix,inId)))

    @staticmethod
    def create_linear_constraint_property(inDocPrefix: str, inId: str,):
        pass

    @staticmethod
    def create_angular_constraint_property(inDocPrefix: str, inId: str,):
        pass

    @staticmethod
    def create_parent_property(inDocPrefix: str, inId: str,) -> OwlNode:
        kb_child = OwlPrefixName("knowrob", "parent")
        rdf_resource = OwlPrefixName("rdf", "resource")
        return OwlNode(kb_child, OwlAttribute(rdf_resource, OwlAttributeValue(inDocPrefix, inId)))

    @staticmethod
    def create_child_property(inDocPrefix: str, inId: str,) -> OwlNode:
        kb_child = OwlPrefixName("knowrob", "child")
        rdf_resource = OwlPrefixName("rdf", "resource")
        return OwlNode(kb_child, OwlAttribute(rdf_resource, OwlAttributeValue(inDocPrefix, inId)))

    @staticmethod
    def create_mobility_property(mobility: str):
        pass

    @staticmethod
    def create_mass_property(mass: float):
        kb_mass = OwlPrefixName("knowrob", "mass")
        rdf_datatype = OwlPrefixName("rdf", "datatype")
        attr_val_float = OwlAttributeValue("xsd", "float")
        return OwlNode(kb_mass, OwlAttribute(rdf_datatype, attr_val_float), str(mass))

    @staticmethod
    def create_physics_properties(mass: float, bGenerateOverlapEvents: bool, bGravity: bool):
        pass

    @staticmethod
    def create_mask_color_property(hexColor: str):
        pass

    @staticmethod
    def create_location_property(inLoc) -> OwlNode:
        kb_translation = OwlPrefixName("knowrob", "translation")
        rdf_datatype = OwlPrefixName("rdf", "datatype")
        attr_val_string = OwlAttributeValue("xsd", "string")

        return OwlNode(kb_translation, OwlAttribute(rdf_datatype, attr_val_string), str(inLoc))

    @staticmethod
    def create_quaternion_property(inQuat) -> OwlNode:
        kb_quat = OwlPrefixName("knowrob", "quaternion")
        rdf_datatype = OwlPrefixName("rdf", "datatype")
        attr_val_string = OwlAttributeValue("xsd", "string")

        return OwlNode(kb_quat, OwlAttribute(rdf_datatype, attr_val_string), str(inQuat))

    @staticmethod
    def create_has_capability_properties(capabilities : List[str]):
        pass

    @staticmethod
    def create_srdl_skeletal_bone_property(inDocPrefix: str, inId: str):
        pass

    @staticmethod
    def create_bone_individual(inDocPrefix: str, inId: str, class_: str, baseLinkId: str, endLinkId: str, boneName: str):
        pass


def create_semantic_map_template(inParams : SemanticMapWriterParams) -> OwlSemanticMap:
    sem_map = OwlSemanticMapStatics.create_default_semantic_map(inParams.id, "log", "ameva_log")
    sem_map.add_semantic_map_individual(inParams.description, inParams.level)



def add_world_individuals(inSemMap : OwlSemanticMap, world : World):
    # ToDo  AddWorldIndividuals
    pass

def write_to_file(world : World, inParams : SemanticMapWriterParams) -> bool:
    full_file_path = os.getcwd() + "/" + inParams.directory_path + "/" + inParams.id + "_SM.owl"

    sem_map : OwlSemanticMap = create_semantic_map_template(inParams)