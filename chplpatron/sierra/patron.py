import json
import pdb
from dateutil.parser import parse as date_parse
from chplpatron.statistics import esutilities
from chplpatron.utilities.baseutilities import hash_email

DO_NOT_INDEX = "DO_NOT_INDEX"


class SierraObject:
    _ignore_attrs = ['to_dict', 'to_es']
    _init_loaded = True
    
    def __init__(self, data=None, init_load=False):
        for key, val in self.__class__.__dict__.items():
            if not key.startswith("_") \
                        and not key.startswith("-")\
                        and key not in self._ignore_attrs:
                # remove class references
                if isinstance(val, list):
                    self.__dict__[key] = []
                    self.__dict__["-" + key] = []
                else:
                    self.__dict__[key] = None
                    self.__dict__["-" + key] = None
        if isinstance(data, dict):
            self._load_dict(data, init_load)
        elif data is not None:
            self._load_raw(data, init_load)
        self.init_loaded = True

    def _load_raw(self, data, init_load=True):
        l_key = list(self.attributes().keys())[0]
        if init_load:
            l_key = "-" + l_key
        setattr(self, l_key, data)

    def _load_dict(self, data, init_load=True):
        for key, val in data.items():
            l_key = key if not init_load else "-" + key
            setattr(self, l_key, val)

    def __setattr__(self, key, value):
        """
        check the class reference to see if the value is an instance of the
        class type as expressed in the class definition
        """
        cls = self.__class__
        l_key = key if not key.startswith("-") else key[1:]
        if key == 'fixedFields':
            x = 1
        try:
            cls_ref = getattr(cls, l_key)
        except AttributeError:
            self.__dict__[key] = value
            return
        if cls_ref is None:
            self.__dict__[key] = value
        elif isinstance(cls_ref, list):
            if len(cls_ref) > 0:
                attr_class = cls_ref[0]
                new_val = self._test_attr(attr_class, value)
                if isinstance(new_val, list):
                    self.__dict__[key] = new_val
                else:
                    self.__dict__[key].append(new_val)
            else:
                if isinstance(value, list):
                    self.__dict__[key] = value
                else:
                    self.__dict__[key].append(value)
        elif isinstance(cls_ref, dict):
            key_type, val_type = list(cls_ref.items())[0]
            if isinstance(value, dict):
                set_val = self.__dict__[key] \
                          if isinstance(self.__dict__[key], dict) \
                          else {}
                for val_key, val_val in value.items():
                    set_val[self._test_attr(key_type, val_key)] = \
                            self._test_attr(val_type, val_val)
                self.__dict__[key] = set_val
        else:
            self.__dict__[key] = self._test_attr(cls_ref, value)

    def _test_attr(self, attr_class, value):
        if isinstance(value, list):
            rtn = []
            for item in value:
                if isinstance(item, attr_class):
                    rtn.append(item)
                else:
                    rtn.append(attr_class(item, not self._init_loaded))
            return rtn
        if isinstance(value, attr_class):
            return value
        try:
            return attr_class(value, not self._init_loaded)
        except (TypeError, ValueError):
            return attr_class(value)

    def attributes(self, all_data=False):
        if all_data:
            return {key: value
                    for key, value in self.__dict__.items()
                    if not key.startswith("_")
                    and key not in self._ignore_attrs}
        return {key: getattr(self, key)
                for key in self.__class__.__dict__.keys()
                if not key.startswith("_") and key not in self._ignore_attrs}

    def __repr__(self):
        val = {key: value.__repr__()
               for key, value in self.attributes().items()
               if value}
        return json.dumps(val, indent=4)

    def to_dict(self, all_data=False):
        rtn = {}
        for key, value in self.attributes(all_data).items():
            if key == 'fixedFields':
                x=1
            if isinstance(value, list):
                r_list = []
                for item in value:
                    val = item if not hasattr(item, 'to_dict') \
                            else item.to_dict()
                    if self._test_none(val):
                        r_list.append(val)
                if len(r_list) > 0:
                    rtn[key] = r_list

            elif isinstance(value, dict):
                r_dict = {}
                for s_key, s_value in value.items():
                    val = s_value if not hasattr(s_value, 'to_dict') \
                            else s_value.to_dict()
                    if self._test_none(val):
                        r_dict[s_key] = val

                rtn[key] = r_dict
            else:
                val = value if not hasattr(value, 'to_dict') \
                        else value.to_dict()
                if self._test_none(val):
                    rtn[key] = val
        return rtn

    def to_es(self, all_data=False):
        rtn = {}
        for key, value in self.attributes(all_data).items():
            if isinstance(value, list):
                r_list = []
                for item in value:
                    val = item if not hasattr(item, 'to_es') \
                            else item.to_dict()
                    if self._test_none(val):
                        r_list.append(val)
                if len(r_list) > 0:
                    rtn[key] = r_list

            elif isinstance(value, dict):
                r_dict = {}
                for s_key, s_value in value.items():
                    val = s_value if not hasattr(s_value, 'to_es') \
                            else s_value.to_dict()
                    if self._test_none(val):
                        r_dict[s_key] = val

                rtn[key] = r_dict
            else:
                val = value if not hasattr(value, 'to_es') \
                        else value.to_dict()
                if self._test_none(val):
                    rtn[key] = val
        return rtn

    @staticmethod
    def _test_none(val):
        if isinstance(val, (dict, list)) and len(val) > 0:
            return True
        elif val is not None:
            return True


class Codes(SierraObject):
    """
    pcode1 (string, optional): a library-defined patron data field,
    pcode2 (string, optional): a library-defined patron data field,
    pcode3 (integer, optional): a library-defined patron data field,
    pcode4 (integer, optional): a library-defined patron data field (CME only)
    """
    pcode1 = str
    pcode2 = str
    pcode3 = str
    pcode4 = str


class Address(SierraObject):
    """
    lines (array[string]): an address line,
    type (Char): the address type (a,h)
    """
    lines = [str]
    type = str
    _type_options = ["a", "h"]
    _required = ['lines', 'type']
    _es_blank = {"city": "unk", "state": "unk"}

    def to_es(self):
        if self.lines:
            try:
                parts = self.lines[-1].split(" ")
                state = parts[-2]
                city = " ".join(parts[:-2]).replace(",", "")
                return {"city": city, "state": state, "addr_type": self.type}
            except IndexError:
                # if unable to parse address pass and return blank address
                pass
        return self._es_blank

    @staticmethod
    def to_es_map():
        return {"address" : {
                    "type": "object",
                    "properties": {
                         "city": "keyword",
                         "state": "keyword",
                         "addr_type": "keyword"
                     }
                    }
                }


class Phone(SierraObject):
    """
    number (string): a phone number,
    type (Char): the phone type (t,p,o)
    """
    number = str
    type = str
    _type_options = ["t", "p", "o"]
    _required = ['number', 'type']

    def to_es(self):
        return None


class Block(SierraObject):
    """
    code (string, optional): a manual patron block code,
    until (string, optional): the date until which the patron is blocked from
    using library services, in ISO 8601 format (yyyy-MM-dd)
    """
    code = str
    until = str
    _required = []


class FixedFieldVal(SierraObject):
    """
    value (T): the value of the field (can be a String, LocalDate, DateTime,
               Boolean, Long, or Decimal depending on the field)
    """
    value = str
    _required = ['value']

    def to_dict(self):
        return self.value

    def to_es(self):
        return self.value


class FixedField(SierraObject):
    """
    label (string): the customizable label for the field,
    value (FixedFieldVal, optional): the stored value of the field (can be a
          String, LocalDate, DateTime, Boolean, Long, or Decimal depending on
          the field),
    display (string, optional): the display value of the field
    """
    label = str
    value = FixedFieldVal
    display = str
    _required = ["label"]
    _ignore_labels = ["BIRTH DATE"]

    def to_es(self):
        if self.label in self._ignore_labels:
            return None
        return {self.label: self.value.to_es()}


class SubField(SierraObject):
    """
    tag (Char): a subfield code,
    content (string): the subfield content
    """
    tag = str
    content = str
    _required = ['tag', 'content']


class VarField(SierraObject):
    """
    fieldTag (Char): the Innovative variable-length field type tag,
    marcTag (string, optional): the MARC tag,
    ind1 (Char, optional): the first MARC indicator, if present,
    ind2 (Char, optional): the second MARC indicator, if present,
    content (string, optional): the field content for varfields with no
                                subfields,
    subfields (array[SubField], optional): a list of subfields, if present
    """
    fieldTag = str
    marcTag = str
    ind1 = str
    ind2 = str
    content = str
    subfields = [SubField]
    _required = ['fieldTag']

    def to_es(self):
        if self.fieldTag in ['x', 'm']:
            return self.to_dict()
        return None


class Patron(SierraObject):
    """
    emails (array[string], optional): a list of the patron's emails
            (must include all applicable email addresses for the patron),
    names (array[string], optional): a list of the patron's names (must
            include all applicable names for the patron),
    addresses (array[Address], optional): a list of the patron's addresses
            (must include all applicable addresses for the patron),
    phones (array[Phone], optional): a list of the patron's phone numbers
            (must include all applicable phone numbers for the patron),
    pin (string, optional): the patron's Personal Identification Number,
    barcodes (array[string], optional): patron's barcode,
    patronType (integer, optional): the patron type code,
    expirationDate (string, optional): the expiration date of the patron's
            borrowing privileges in ISO 8601 format (yyyy-MM-dd),
    birthDate (string, optional): the patron's date of birth in ISO 8601
            format (yyyy-MM-dd),
    patronCodes (Codes, optional): a list of patron codes,
    blockInfo (Block, optional): patron block information,
    uniqueIds (array[string], optional): the patron's unique IDs,
    pMessage (string, optional): the patron's message,
    homeLibraryCode (string, optional): the patron's home library,
    langPref (string, optional): the patron's language preference,
    fixedFields (map[integer, FixedField], optional): the fixed-length
            fields from the patron record,
    varFields (array[VarField], optional): the variable-length fields
            from the patron record
    """
    _required = []
    emails = [str]
    names = [str]
    addresses = [Address]
    phones = [Phone]
    pin = str
    barcodes = [str]
    patronType = int
    expirationDate = str
    birthDate = str
    patronCodes = Codes
    blockInfo = Block
    uniqueIds = [str]
    pMessage = str
    homeLibraryCode = str
    langPref = str
    fixedFields = {int: FixedField}
    varFields = [VarField]
    _es_ignore = ["uniqueIds", "phones", "names", "pin", "barcodes"]

    def to_es(self):
        rtn = {}
        for key, value in self.attributes(True).items():
            if key in self._es_ignore:
                continue
            if key == 'emails':
                rtn_list = []
                for email in value:
                    rtn_list.append(hash_email(email))
                if rtn_list:
                    rtn[key] = rtn_list
            elif isinstance(value, list):
                rtn_list = []
                for item in value:
                    try:
                        conv = item.to_es()
                        if conv:
                            rtn_list.append(conv)
                    except AttributeError:
                        if item:
                            rtn_list.append(item)
                if rtn_list:
                    rtn[key] = rtn_list
            elif isinstance(value, dict):
                rtn_dict = {}
                # this applies for FixedFields and we will ignore the key number
                for item_key, item_value in value.items():
                    try:
                        conv_item = item_value.to_es()
                    except AttributeError:
                        conv_item = item_value
                    if not conv_item:
                        continue
                    try:
                        for ky, val in conv_item.items():
                            rtn_dict[ky] = val
                    except AttributeError:
                        rtn_dict[item_key] = conv_item
                if rtn_dict:
                    rtn[key] = rtn_dict
            elif key == 'birthDate':
                if not value:
                    continue
                conv = esutilities\
                    .conv_to_age_range(esutilities
                                       .conv_birthdate_to_age(
                                        date_parse(value)))
                if conv:
                    rtn["age_range"] = conv
            else:
                try:
                    conv = value.to_es()
                    if conv:
                        rtn[key] = conv
                except AttributeError:
                    if value:
                        rtn[key] = value
        return rtn


