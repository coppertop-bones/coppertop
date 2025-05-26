




from bones.lang._type_lang.jones_type_manager import BTypeError


bmtnul = 0      # i.e. not initialised yet
bmtatm = 1      # snuggled in the highest nibble in the type's metadata, i.e. 0x1000_0000

bmtint = 2
bmtuni = 3

bmttup = 4
bmtstr = 5
bmtrec = 6

bmtseq = 7
bmtmap = 8
bmtfnc = 9

bmtsvr = 10


bmtnameById = {
    bmtnul: 'TBC',
    bmtatm: 'Atom',
    bmtint: 'Inter',
    bmtuni: 'Union',
    bmttup: 'Tuple',
    bmtstr: 'Struct',
    bmtrec: 'Rec',
    bmtseq: 'Seq',
    bmtmap: 'Map',
    bmtfnc: 'Fn',
    bmtsvr: 'T',
}


class TLError(Exception): pass
class SchemaError(BTypeError): pass