# -*- coding: utf-8 -*-
from itertools import count
from uuid import uuid4

from cadnano import util
from cadnano import preferences as prefs
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.cnproxy import UndoCommand
from cadnano.enum import PointType
from cadnano.cnobject import CNObject
from .changeviewpropertycmd import ChangeViewPropertyCommand

class Part(CNObject):
    """A Part is a group of VirtualHelix items that are on the same lattice.
    Parts are the model component that most directly corresponds to a
    DNA origami design.

    Parts are always parented to the document.
    Parts know about their oligos, and the internal geometry of a part
    Copying a part recursively copies all elements in a part: StrandSets,
    Strands, etc

    PartInstances are parented to either the document or an assembly
    PartInstances know global position of the part
    Copying a PartInstance only creates a new PartInstance with the same
    Part(), with a mutable parent and position field.
    """
    editable_properties = ['name', 'color', 'grid_type']

    def __init__(self, *args, **kwargs):
        """Sets the parent document, sets bounds for part dimensions, and sets up
        bookkeeping for partInstances, Oligos, VirtualHelix's, and helix ID
        number assignment.
        """
        self._document = document = kwargs.get('document', None)
        super(Part, self).__init__(document)
        self._instance_count = 0
        # Properties
        self.view_properties = {}

        # TODO document could be None
        self._group_properties = {  'name':         "Part%d" % len(document.children()),
                                    'color':        "#000000", # outlinerview will override from styles
                                    'is_visible':   True
                                }

        self.uuid = kwargs['uuid'] if 'uuid' in kwargs else uuid4().hex

        # Selections
        self._selections = {}

        if self.__class__ == Part:
            e = "This class is abstract. Perhaps you want HoneycombPart."
            raise NotImplementedError(e)
    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<%s %s>" % (cls_name, str(id(self))[-4:])

    ### SIGNALS ###
    # A. Part
    partZDimensionsChangedSignal = ProxySignal(CNObject, int, int, bool, # self, id_min, id_max, zoom to fit
                        name='partZDimensionsChangedSignal')     # self
    partInstanceAddedSignal = ProxySignal(CNObject,
                        name='partInstanceAddedSignal')         # self
    partParentChangedSignal = ProxySignal(CNObject,
                        name='partParentChangedSignal')         # self
    partRemovedSignal = ProxySignal(CNObject,
                        name='partRemovedSignal')               # self
    partPropertyChangedSignal = ProxySignal(CNObject, object, object,
                        name='partPropertyChangedSignal')       # self, property_name, new_value
    partSelectedChangedSignal = ProxySignal(CNObject, object,
                        name='partSelectedChangedSignal')       # self, is_selected
    partActiveChangedSignal = ProxySignal(CNObject, bool,       # self, is_active
                        name='partActiveChangedSignal')
    partViewPropertySignal = ProxySignal(CNObject, str, str, object,    # self, view, key, val
                                name='partViewPropertySignal')

    # E.
    partDocumentSettingChangedSignal = ProxySignal(object, str, object, # self, key, value
                                    name='partDocumentSettingChangedSignal')

    ### SLOTS ###

    ### ACCESSORS ###
    def document(self):
        return self._document
    # end def

    def setDocument(self, document):
        self._document = document
    # end def

    def incrementInstance(self, document):
        self._instance_count += 1
        if self._instance_count == 1:
            self._document = document
            document.addChild(self)
    # end def

    def decrementInstance(self):
        ic = self._instance_count
        if ic == 0:
            raise IndexError("Can't have less than zero instance of a Part")
        ic -= 1
        if ic == 0:
            self._document = None
            self._document.removeChild(self)
        self._instance_count = ic
    # end def

    def getProperty(self, key):
        return self._group_properties[key]
    # end def

    def getOutlineProperties(self):
        props = self._group_properties
        return props['name'], props['color'], props['is_visible']
    # end def

    def getColor(self):
        return self._group_properties['color']

    def setViewProperty(self, key, value):
        self.view_properties[key] = value
    # end def

    def getViewProperty(self, key):
        return self.view_properties[key]
    # end def

    def getName(self):
        return self._group_properties['name']
    # end def

    def getPropertyDict(self):
        return self._group_properties
    # end def

    def setProperty(self, key, value):
        # use ModifyPropertyCommand here
        self._group_properties[key] = value
        self.partPropertyChangedSignal.emit(self, key, value)
    # end def

    def changeViewProperty(self, view, key, value, use_undostack=True):
        c = ChangeViewPropertyCommand(self, view, key, value)
        util.execCommandList(self, [c],
                             desc="Change Part View Property `%s`" % key,
                             use_undostack=use_undostack)
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
    # end def
# end class
