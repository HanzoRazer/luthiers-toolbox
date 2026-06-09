# RECOVERY — 8J Pocketing Intent Lane (from orphaned bytecode)

**Created:** 2026-06-08  
**Why this exists:** the 8J pocketing CamIntentV1 lane was built+compiled 2026-05-25 (same
session as 8H) but the `.py` source was **never committed and is lost**. Only orphaned `.pyc`
bytecode survived in `__pycache__` (Python 3.14). This doc preserves the recovered content in
git **before a `git clean`/cache-sweep erases the only copy** (the 8I evaporation mode, caught
in progress). Source of truth for the eventual reconstruction — the `.pyc` is what was actually
built, and it **refutes** the speculative 8J dev-order schema (no feed_rate/spindle_rpm/
entry_strategy; instead islands/roughing_only/finish_allowance_mm).

**Recovery method:** `marshal.load` (skip 16-byte header) + `dis.dis`. Full source-level
decompilation isn't available for 3.14, but disassembly + const/name/string extraction recovers
every field, validator, threshold, error message, and the endpoint.

---

## `cam/pocketing/intent_schema`  
`app/cam/pocketing/__pycache__/intent_schema.cpython-314.pyc` — 6013 bytes, mtime(UTC) 2026-05-25T19:11:45.068646

### Recovered structure (names + string constants)
```
<<module>> names=['__doc__', '__future__', 'annotations', 'typing', 'List', 'Optional', 'pydantic', 'BaseModel', 'Field', 'field_validator', 'model_validator', 'PocketPointV1', 'PocketIslandV1', 'PocketDesignV1', 'validate_pocket_design']
  str: 'PocketPointV1'
  str: 'PocketIslandV1'
  str: 'PocketDesignV1'
  <PocketPointV1> names=['__name__', '__module__', '__qualname__', '__firstlineno__', '__doc__', 'Field', 'x', '__annotations__', 'y', '__static_attributes__']
    str: 'PocketPointV1'
    str: 'A 2D point in the pocket boundary or island.'
    str: 'X coordinate in mm'
    str: 'float'
    str: 'x'
    str: 'Y coordinate in mm'
    str: 'y'
  <PocketIslandV1> names=['__name__', '__module__', '__qualname__', '__firstlineno__', '__doc__', 'Field', 'boundary', '__annotations__', 'field_validator', 'classmethod', 'validate_boundary_length', '__static_attributes__']
    str: 'PocketIslandV1'
    str: 'An island (no-cut region) within the pocket.'
    str: 'Island boundary as list of points'
    str: 'List[PocketPointV1]'
    str: 'boundary'
    <__annotate__> names=[]
      str: 'v'
      str: 'List[PocketPointV1]'
      str: 'return'
    <validate_boundary_length> names=['len', 'ValueError']
      str: 'Validate island boundary has at least 3 points.'
      str: 'Island boundary must have at least 3 points'
  <PocketDesignV1> names=['__name__', '__module__', '__qualname__', '__firstlineno__', '__doc__', 'Field', 'boundary', '__annotations__', 'list', 'islands', 'pocket_depth_mm', 'tool_diameter_mm', 'stepover_percent', 'roughing_only', 'finish_pass', 'finish_allowance_mm', 'field_validator', 'classmethod', 'validate_boundary_length', 'model_validator', 'validate_finish_coherence', '__static_attributes__']
    str: 'PocketDesignV1'
    str: 'Pocket boundary as list of points (must form simple polygon)'
    str: 'List[PocketPointV1]'
    str: 'boundary'
    str: 'Islands (no-cut regions) within the pocket'
    str: 'List[PocketIslandV1]'
    str: 'islands'
    str: 'Total pocket depth in mm'
    str: 'float'
    str: 'pocket_depth_mm'
    str: 'Tool diameter in mm (L.1 range: 0.5-50mm)'
    str: 'tool_diameter_mm'
    str: 'Stepover as percentage of tool diameter (30-70%)'
    str: 'stepover_percent'
    str: 'If True, skip finishing pass'
    str: 'bool'
    str: 'roughing_only'
    str: 'Whether to include a finishing pass'
    str: 'finish_pass'
    str: 'Material left for finishing pass (mm)'
    str: 'finish_allowance_mm'
    str: 'after'
    <__annotate__> names=[]
      str: 'v'
      str: 'List[PocketPointV1]'
      str: 'return'
    <validate_boundary_length> names=['len', 'ValueError']
      str: 'Validate boundary has at least 3 points.'
      str: 'Boundary must have at least 3 points'
    <__annotate__> names=[]
      str: 'return'
      str: "'PocketDesignV1'"
    <validate_finish_coherence> names=['roughing_only', 'finish_pass', 'object', '__setattr__']
      str: 'Validate finishing configuration coherence.'
      str: 'finish_pass'
  <__annotate__> names=[]
    str: 'design_dict'
    str: 'dict'
    str: 'return'
    str: 'PocketDesignV1'
  <validate_pocket_design> names=['PocketDesignV1', 'Exception', 'ValueError']
    str: 'Invalid Pocketing design: '
```

### Full disassembly (`dis.dis`)
```
  0           RESUME                   0

  1           LOAD_CONST               0 ("\nPocketing Design Schema for CamIntentV1\n\nDefines PocketDesignV1 for the design bucket of pocketing operations.\n\nThis schema describes WHAT to pocket (boundary, islands, depth, tool),\nnot HOW to pocket it (feed rates, spindle, strategy).\n\nPart of the CAM Intent First-Endpoint Migration (ADR-003).\n\nScope (8J):\n- entry_strategy: EXCLUDED - no L.1 core support (same as coolant_mode in 8I)\n- stepover_percent: bounded to [30, 70] to match L.1's actual range\n")
              STORE_NAME               0 (__doc__)

 15           LOAD_SMALL_INT           0
              LOAD_CONST               1 (('annotations',))
              IMPORT_NAME              1 (__future__)
              IMPORT_FROM              2 (annotations)
              STORE_NAME               2 (annotations)
              POP_TOP

 17           LOAD_SMALL_INT           0
              LOAD_CONST               2 (('List', 'Optional'))
              IMPORT_NAME              3 (typing)
              IMPORT_FROM              4 (List)
              STORE_NAME               4 (List)
              IMPORT_FROM              5 (Optional)
              STORE_NAME               5 (Optional)
              POP_TOP

 19           LOAD_SMALL_INT           0
              LOAD_CONST               3 (('BaseModel', 'Field', 'field_validator', 'model_validator'))
              IMPORT_NAME              6 (pydantic)
              IMPORT_FROM              7 (BaseModel)
              STORE_NAME               7 (BaseModel)
              IMPORT_FROM              8 (Field)
              STORE_NAME               8 (Field)
              IMPORT_FROM              9 (field_validator)
              STORE_NAME               9 (field_validator)
              IMPORT_FROM             10 (model_validator)
              STORE_NAME              10 (model_validator)
              POP_TOP

 22           LOAD_BUILD_CLASS
              PUSH_NULL
              LOAD_CONST               4 (<code object PocketPointV1 at 0x0000024B1C63EFB0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 22>)
              MAKE_FUNCTION
              LOAD_CONST               5 ('PocketPointV1')
              LOAD_NAME                7 (BaseModel)
              CALL                     3
              STORE_NAME              11 (PocketPointV1)

 29           LOAD_BUILD_CLASS
              PUSH_NULL
              LOAD_CONST               6 (<code object PocketIslandV1 at 0x0000024B1C684DF0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 29>)
              MAKE_FUNCTION
              LOAD_CONST               7 ('PocketIslandV1')
              LOAD_NAME                7 (BaseModel)
              CALL                     3
              STORE_NAME              12 (PocketIslandV1)

 47           LOAD_BUILD_CLASS
              PUSH_NULL
              LOAD_CONST               8 (<code object PocketDesignV1 at 0x0000024B1C3F85C0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 47>)
              MAKE_FUNCTION
              LOAD_CONST               9 ('PocketDesignV1')
              LOAD_NAME                7 (BaseModel)
              CALL                     3
              STORE_NAME              13 (PocketDesignV1)

130           LOAD_CONST              10 (<code object __annotate__ at 0x0000024B1C70CC60, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 130>)
              MAKE_FUNCTION
              LOAD_CONST              11 (<code object validate_pocket_design at 0x0000024B1C63F0E0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 130>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              14 (validate_pocket_design)
              LOAD_CONST              12 (None)
              RETURN_VALUE

Disassembly of <code object PocketPointV1 at 0x0000024B1C63EFB0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 22>:
 22           RESUME                   0
              LOAD_NAME                0 (__name__)
              STORE_NAME               1 (__module__)
              LOAD_CONST               0 ('PocketPointV1')
              STORE_NAME               2 (__qualname__)
              LOAD_SMALL_INT          22
              STORE_NAME               3 (__firstlineno__)
              SETUP_ANNOTATIONS

 23           LOAD_CONST               1 ('A 2D point in the pocket boundary or island.')
              STORE_NAME               4 (__doc__)

 25           LOAD_NAME                5 (Field)
              PUSH_NULL
              LOAD_CONST               2 (Ellipsis)
              LOAD_CONST               3 ('X coordinate in mm')
              LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME               6 (x)
              LOAD_CONST               5 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST               6 ('x')
              STORE_SUBSCR

 26           LOAD_NAME                5 (Field)
              PUSH_NULL
              LOAD_CONST               2 (Ellipsis)
              LOAD_CONST               7 ('Y coordinate in mm')
              LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME               8 (y)
              LOAD_CONST               5 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST               8 ('y')
              STORE_SUBSCR
              LOAD_CONST               9 (())
              STORE_NAME               9 (__static_attributes__)
              LOAD_CONST              10 (None)
              RETURN_VALUE

Disassembly of <code object PocketIslandV1 at 0x0000024B1C684DF0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 29>:
 29           RESUME                   0
              LOAD_NAME                0 (__name__)
              STORE_NAME               1 (__module__)
              LOAD_CONST               0 ('PocketIslandV1')
              STORE_NAME               2 (__qualname__)
              LOAD_SMALL_INT          29
              STORE_NAME               3 (__firstlineno__)
              SETUP_ANNOTATIONS

 30           LOAD_CONST               1 ('An island (no-cut region) within the pocket.')
              STORE_NAME               4 (__doc__)

 32           LOAD_NAME                5 (Field)
              PUSH_NULL

 33           LOAD_CONST               2 (Ellipsis)

 34           LOAD_CONST               3 ('Island boundary as list of points')

 35           LOAD_SMALL_INT           3

 32           LOAD_CONST               4 (('description', 'min_length'))
              CALL_KW                  3
              STORE_NAME               6 (boundary)
              LOAD_CONST               5 ('List[PocketPointV1]')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST               6 ('boundary')
              STORE_SUBSCR

 38           LOAD_NAME                8 (field_validator)
              PUSH_NULL
              LOAD_CONST               6 ('boundary')
              CALL                     1

 39           LOAD_NAME                9 (classmethod)

 40           LOAD_CONST               7 (<code object __annotate__ at 0x0000024B1C5EBE10, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 40>)
              MAKE_FUNCTION
              LOAD_CONST               8 (<code object validate_boundary_length at 0x0000024B1C696780, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 38>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)

 39           CALL                     0

 38           CALL                     0

 40           STORE_NAME              10 (validate_boundary_length)
              LOAD_CONST               9 (())
              STORE_NAME              11 (__static_attributes__)
              LOAD_CONST              10 (None)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C5EBE10, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 40>:
 40           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('v')
              LOAD_CONST               2 ('List[PocketPointV1]')
              LOAD_CONST               3 ('return')
              LOAD_CONST               2 ('List[PocketPointV1]')
              BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object validate_boundary_length at 0x0000024B1C696780, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 38>:
 38           RESUME                   0

 42           LOAD_GLOBAL              1 (len + NULL)
              LOAD_FAST_BORROW         1 (v)
              CALL                     1
              LOAD_SMALL_INT           3
              COMPARE_OP              18 (bool(<))
              POP_JUMP_IF_FALSE       12 (to L1)
              NOT_TAKEN

 43           LOAD_GLOBAL              3 (ValueError + NULL)
              LOAD_CONST               1 ('Island boundary must have at least 3 points')
              CALL                     1
              RAISE_VARARGS            1

 44   L1:     LOAD_FAST_BORROW         1 (v)
              RETURN_VALUE

Disassembly of <code object PocketDesignV1 at 0x0000024B1C3F85C0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 47>:
 47           RESUME                   0
              LOAD_NAME                0 (__name__)
              STORE_NAME               1 (__module__)
              LOAD_CONST               0 ('PocketDesignV1')
              STORE_NAME               2 (__qualname__)
              LOAD_SMALL_INT          47
              STORE_NAME               3 (__firstlineno__)
              SETUP_ANNOTATIONS

 48           LOAD_CONST               1 ('\nDesign specification for a pocketing operation.\n\nContains only design-defining fields (the "what"):\n- boundary geometry (must be a simple, non-self-intersecting polygon)\n- islands (no-cut regions, must be valid and within boundary)\n- pocket depth\n- tool geometry\n- stepover (bounded to L.1\'s valid range: 30-70%)\n- roughing/finishing configuration\n')
              STORE_NAME               4 (__doc__)

 61           LOAD_NAME                5 (Field)
              PUSH_NULL

 62           LOAD_CONST               2 (Ellipsis)

 63           LOAD_CONST               3 ('Pocket boundary as list of points (must form simple polygon)')

 64           LOAD_SMALL_INT           3

 61           LOAD_CONST               4 (('description', 'min_length'))
              CALL_KW                  3
              STORE_NAME               6 (boundary)
              LOAD_CONST               5 ('List[PocketPointV1]')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST               6 ('boundary')
              STORE_SUBSCR

 68           LOAD_NAME                5 (Field)
              PUSH_NULL

 69           LOAD_NAME                8 (list)

 70           LOAD_CONST               7 ('Islands (no-cut regions) within the pocket')

 68           LOAD_CONST               8 (('default_factory', 'description'))
              CALL_KW                  2
              STORE_NAME               9 (islands)
              LOAD_CONST               9 ('List[PocketIslandV1]')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              10 ('islands')
              STORE_SUBSCR

 74           LOAD_NAME                5 (Field)
              PUSH_NULL

 75           LOAD_CONST               2 (Ellipsis)

 76           LOAD_SMALL_INT           0

 77           LOAD_CONST              11 (100.0)

 78           LOAD_CONST              12 ('Total pocket depth in mm')

 74           LOAD_CONST              13 (('gt', 'le', 'description'))
              CALL_KW                  4
              STORE_NAME              10 (pocket_depth_mm)
              LOAD_CONST              14 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              15 ('pocket_depth_mm')
              STORE_SUBSCR

 82           LOAD_NAME                5 (Field)
              PUSH_NULL

 83           LOAD_CONST               2 (Ellipsis)

 84           LOAD_CONST              16 (0.5)

 85           LOAD_CONST              17 (50.0)

 86           LOAD_CONST              18 ('Tool diameter in mm (L.1 range: 0.5-50mm)')

 82           LOAD_CONST              13 (('gt', 'le', 'description'))
              CALL_KW                  4
              STORE_NAME              11 (tool_diameter_mm)
              LOAD_CONST              14 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              19 ('tool_diameter_mm')
              STORE_SUBSCR

 90           LOAD_NAME                5 (Field)
              PUSH_NULL

 91           LOAD_CONST              20 (40.0)

 92           LOAD_CONST              21 (30.0)

 93           LOAD_CONST              22 (70.0)

 94           LOAD_CONST              23 ('Stepover as percentage of tool diameter (30-70%)')

 90           LOAD_CONST              24 (('ge', 'le', 'description'))
              CALL_KW                  4
              STORE_NAME              12 (stepover_percent)
              LOAD_CONST              14 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              25 ('stepover_percent')
              STORE_SUBSCR

 98           LOAD_NAME                5 (Field)
              PUSH_NULL

 99           LOAD_CONST              26 (False)

100           LOAD_CONST              27 ('If True, skip finishing pass')

 98           LOAD_CONST              28 (('description',))
              CALL_KW                  2
              STORE_NAME              13 (roughing_only)
              LOAD_CONST              29 ('bool')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              30 ('roughing_only')
              STORE_SUBSCR

102           LOAD_NAME                5 (Field)
              PUSH_NULL

103           LOAD_CONST              31 (True)

104           LOAD_CONST              32 ('Whether to include a finishing pass')

102           LOAD_CONST              28 (('description',))
              CALL_KW                  2
              STORE_NAME              14 (finish_pass)
              LOAD_CONST              29 ('bool')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              33 ('finish_pass')
              STORE_SUBSCR

106           LOAD_NAME                5 (Field)
              PUSH_NULL

107           LOAD_CONST              34 (0.25)

108           LOAD_CONST              35 (0.0)

109           LOAD_CONST              36 (5.0)

110           LOAD_CONST              37 ('Material left for finishing pass (mm)')

106           LOAD_CONST              24 (('ge', 'le', 'description'))
              CALL_KW                  4
              STORE_NAME              15 (finish_allowance_mm)
              LOAD_CONST              14 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              38 ('finish_allowance_mm')
              STORE_SUBSCR

113           LOAD_NAME               16 (field_validator)
              PUSH_NULL
              LOAD_CONST               6 ('boundary')
              CALL                     1

114           LOAD_NAME               17 (classmethod)

115           LOAD_CONST              39 (<code object __annotate__ at 0x0000024B1C70CA80, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 115>)
              MAKE_FUNCTION
              LOAD_CONST              40 (<code object validate_boundary_length at 0x0000024B1C696CD0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 113>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)

114           CALL                     0

113           CALL                     0

115           STORE_NAME              18 (validate_boundary_length)

121           LOAD_NAME               19 (model_validator)
              PUSH_NULL
              LOAD_CONST              41 ('after')
              LOAD_CONST              42 (('mode',))
              CALL_KW                  1

122           LOAD_CONST              43 (<code object __annotate__ at 0x0000024B1C70CB70, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 122>)
              MAKE_FUNCTION
              LOAD_CONST              44 (<code object validate_finish_coherence at 0x0000024B1C627360, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 121>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)

121           CALL                     0

122           STORE_NAME              20 (validate_finish_coherence)
              LOAD_CONST              45 (())
              STORE_NAME              21 (__static_attributes__)
              LOAD_CONST              46 (None)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C70CA80, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 115>:
115           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('v')
              LOAD_CONST               2 ('List[PocketPointV1]')
              LOAD_CONST               3 ('return')
              LOAD_CONST               2 ('List[PocketPointV1]')
              BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object validate_boundary_length at 0x0000024B1C696CD0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 113>:
113           RESUME                   0

117           LOAD_GLOBAL              1 (len + NULL)
              LOAD_FAST_BORROW         1 (v)
              CALL                     1
              LOAD_SMALL_INT           3
              COMPARE_OP              18 (bool(<))
              POP_JUMP_IF_FALSE       12 (to L1)
              NOT_TAKEN

118           LOAD_GLOBAL              3 (ValueError + NULL)
              LOAD_CONST               1 ('Boundary must have at least 3 points')
              CALL                     1
              RAISE_VARARGS            1

119   L1:     LOAD_FAST_BORROW         1 (v)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C70CB70, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 122>:
122           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('return')
              LOAD_CONST               2 ("'PocketDesignV1'")
              BUILD_MAP                1
              RETURN_VALUE

Disassembly of <code object validate_finish_coherence at 0x0000024B1C627360, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 121>:
121           RESUME                   0

124           LOAD_FAST_BORROW         0 (self)
              LOAD_ATTR                0 (roughing_only)
              TO_BOOL
              POP_JUMP_IF_FALSE       42 (to L1)
              NOT_TAKEN
              LOAD_FAST_BORROW         0 (self)
              LOAD_ATTR                2 (finish_pass)
              TO_BOOL
              POP_JUMP_IF_FALSE       24 (to L1)
              NOT_TAKEN

126           LOAD_GLOBAL              4 (object)
              LOAD_ATTR                7 (__setattr__ + NULL|self)
              LOAD_FAST_BORROW         0 (self)
              LOAD_CONST               1 ('finish_pass')
              LOAD_CONST               2 (False)
              CALL                     3
              POP_TOP

127   L1:     LOAD_FAST_BORROW         0 (self)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C70CC60, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 130>:
130           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('design_dict')
              LOAD_CONST               2 ('dict')
              LOAD_CONST               3 ('return')
              LOAD_CONST               4 ('PocketDesignV1')
              BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object validate_pocket_design at 0x0000024B1C63F0E0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_schema.py", line 130>:
 130           RESUME                   0

 143           NOP

 144   L1:     LOAD_GLOBAL              1 (PocketDesignV1 + NULL)
               LOAD_CONST               3 (())
               BUILD_MAP                0
               LOAD_FAST_BORROW         0 (design_dict)
               DICT_MERGE               1
               CALL_FUNCTION_EX
       L2:     RETURN_VALUE

  --   L3:     PUSH_EXC_INFO

 145           LOAD_GLOBAL              2 (Exception)
               CHECK_EXC_MATCH
               POP_JUMP_IF_FALSE       21 (to L6)
               NOT_TAKEN
               STORE_FAST               1 (e)

 146   L4:     LOAD_GLOBAL              5 (ValueError + NULL)
               LOAD_CONST               1 ('Invalid Pocketing design: ')
               LOAD_FAST                1 (e)
               FORMAT_SIMPLE
               BUILD_STRING             2
               CALL                     1
               LOAD_FAST                1 (e)
               RAISE_VARARGS            2

  --   L5:     LOAD_CONST               2 (None)
               STORE_FAST               1 (e)
               DELETE_FAST              1 (e)
               RERAISE                  1

 145   L6:     RERAISE                  0

  --   L7:     COPY                     3
               POP_EXCEPT
               RERAISE                  1
ExceptionTable:
  L1 to L2 -> L3 [0]
  L3 to L4 -> L7 [1] lasti
  L4 to L5 -> L5 [1] lasti
  L5 to L7 -> L7 [1] lasti

```
---

## `cam/pocketing/feasibility`  
`app/cam/pocketing/__pycache__/feasibility.cpython-314.pyc` — 14216 bytes, mtime(UTC) 2026-05-25T19:11:46.300815

### Recovered structure (names + string constants)
```
<<module>> names=['__doc__', '__future__', 'annotations', 'hashlib', 'json', 'dataclasses', 'dataclass', 'field', 'typing', 'Any', 'Dict', 'List', 'Tuple', 'shapely.geometry', 'Polygon', 'shapely.validation', 'explain_validity', 'PocketFeasibilityResult', '_points_to_coords', '_validate_polygon_geometry', '_validate_island_within_boundary', '_validate_islands_non_overlapping', 'compute_pocket_area', 'compute_pocket_feasibility', 'hash_feasibility_result']
  str: 'PocketFeasibilityResult'
  <PocketFeasibilityResult> names=['__name__', '__module__', '__qualname__', '__firstlineno__', '__doc__', '__annotations__', 'field', 'list', 'issues', 'warnings', 'dict', 'summary', 'to_dict', '__static_attributes__']
    str: 'PocketFeasibilityResult'
    str: 'Result of pocketing feasibility check.'
    str: 'bool'
    str: 'feasible'
    str: 'str'
    str: 'risk_level'
    str: 'List[str]'
    str: 'issues'
    str: 'warnings'
    str: 'Dict[str, Any]'
    str: 'summary'
    <__annotate__> names=[]
      str: 'return'
      str: 'Dict[str, Any]'
    <to_dict> names=['feasible', 'risk_level', 'issues', 'warnings', 'summary']
      str: 'feasible'
      str: 'risk_level'
      str: 'issues'
      str: 'warnings'
      str: 'summary'
  <__annotate__> names=[]
    str: 'points'
    str: 'List[Tuple[float, float]]'
    str: 'return'
  <_points_to_coords> names=[]
    str: 'Convert point list to coordinate tuples for Shapely.'
  <__annotate__> names=[]
    str: 'coords'
    str: 'List[Tuple[float, float]]'
    str: 'name'
    str: 'str'
    str: 'return'
    str: 'Tuple[bool, str]'
  <_validate_polygon_geometry> names=['len', 'Polygon', 'is_valid', 'explain_validity', 'is_empty', 'Exception', 'str']
    str: ' must have at least 3 points'
    str: ' is not a valid polygon: '
    str: ' is empty'
    str: ' geometry error: '
  <__annotate__> names=[]
    str: 'boundary_coords'
    str: 'List[Tuple[float, float]]'
    str: 'island_coords'
    str: 'island_index'
    str: 'int'
    str: 'return'
    str: 'Tuple[bool, str]'
  <_validate_island_within_boundary> names=['Polygon', 'contains', 'intersects', 'Exception', 'str']
    str: 'island '
    str: ' extends outside boundary'
    str: ' is not within boundary'
    str: ' containment check failed: '
  <__annotate__> names=[]
    str: 'islands_coords'
    str: 'List[List[Tuple[float, float]]]'
    str: 'return'
    str: 'Tuple[bool, str]'
  <_validate_islands_non_overlapping> names=['len', 'Polygon', 'range', 'intersects', 'intersection', 'area', 'Exception', 'str']
    str: 'islands '
    str: ' and '
    str: ' overlap'
    str: 'island overlap check failed: '
  <__annotate__> names=[]
    str: 'boundary_coords'
    str: 'List[Tuple[float, float]]'
    str: 'islands_coords'
    str: 'List[List[Tuple[float, float]]]'
    str: 'return'
    str: 'float'
  <compute_pocket_area> names=['Polygon', 'area', 'sum']
    <<genexpr>> names=['Polygon', 'area']
  <__annotate__> names=[]
    str: 'boundary'
    str: 'List[Tuple[float, float]]'
    str: 'islands'
    str: 'List[List[Tuple[float, float]]]'
    str: 'pocket_depth_mm'
    str: 'float'
    str: 'tool_diameter_mm'
    str: 'stepover_percent'
    str: 'feed_rate_mm_min'
    str: 'plunge_rate_mm_min'
    str: 'safe_z_mm'
    str: 'retract_z_mm'
    str: 'stepdown_mm'
    str: 'finish_allowance_mm'
    str: 'return'
    str: 'PocketFeasibilityResult'
  <compute_pocket_feasibility> names=['_validate_polygon_geometry', 'append', 'enumerate', '_validate_island_within_boundary', '_validate_islands_non_overlapping', 'max', 'int', 'compute_pocket_area', 'len', 'round', 'PocketFeasibilityResult']
    str: 'boundary'
    str: 'island '
    str: 'tool_diameter_mm must be > 0'
    str: 'tool_diameter_mm='
    str: 'mm below L.1 minimum (0.5mm)'
    str: 'mm above L.1 maximum (50mm)'
    str: 'stepover_percent='
    str: '% below L.1 minimum (30%)'
    str: '% above L.1 maximum (70%)'
    str: '% is aggressive - may leave scallops'
    str: 'pocket_depth_mm must be > 0'
    str: 'pocket_depth_mm='
    str: 'mm is very deep'
    str: 'stepdown_mm must be > 0'
    str: 'stepdown_mm='
    str: 'mm exceeds tool diameter - aggressive'
    str: 'feed_rate_mm_min must be > 0'
    str: 'plunge_rate_mm_min must be > 0'
    str: 'plunge_rate exceeds feed_rate - unusual'
    str: 'safe_z_mm must be > 0'
    str: 'retract_z_mm must be > 0'
    str: 'retract_z_mm > safe_z_mm - will use safe_z'
    str: 'finish_allowance_mm must be >= 0'
    str: 'finish_allowance exceeds tool radius'
    str: 'Deep pocket: depth/diameter ratio is '
    str: '.1f'
    str: '. Verify tool flute length and chip evacuation.'
    str: 'Estimated '
    str: ' passes - consider larger stepdown'
    str: 'blocked'
    str: 'high'
    str: 'medium'
    str: 'low'
    str: 'pocket_area_mm2'
    str: 'island_count'
    str: 'estimated_pass_count'
    str: 'tool_diameter_mm'
    str: 'stepover_percent'
    str: 'pocket_depth_mm'
  <__annotate__> names=[]
    str: 'result'
    str: 'PocketFeasibilityResult'
    str: 'return'
    str: 'str'
  <hash_feasibility_result> names=['json', 'dumps', 'to_dict', 'hashlib', 'sha256', 'encode', 'hexdigest']
    str: 'Generate SHA256 hash of feasibility result for provenance.'
```

### Full disassembly (`dis.dis`)
```
  0           RESUME                   0

  1           LOAD_CONST               0 ('\nPocketing Feasibility Check\n\nFeasibility validation for pocketing operations.\nPart of the OPERATION lane requirements (8J).\n\nThis implements the four geometric validity checks required by 8J:\n1. Boundary is a valid simple polygon (non-self-intersecting)\n2. Each island is a valid simple polygon\n3. Each island lies fully within the boundary\n4. Islands do not overlap each other\n\nAll four are BLOCKING issues, not warnings.\n\nAdditional checks:\n- Tool diameter sanity\n- Stepover in L.1 range\n- Safe/retract Z above material\n- Deep pocket/tool ratio warnings\n')
              STORE_NAME               0 (__doc__)

 21           LOAD_SMALL_INT           0
              LOAD_CONST               1 (('annotations',))
              IMPORT_NAME              1 (__future__)
              IMPORT_FROM              2 (annotations)
              STORE_NAME               2 (annotations)
              POP_TOP

 23           LOAD_SMALL_INT           0
              LOAD_CONST               2 (None)
              IMPORT_NAME              3 (hashlib)
              STORE_NAME               3 (hashlib)

 24           LOAD_SMALL_INT           0
              LOAD_CONST               2 (None)
              IMPORT_NAME              4 (json)
              STORE_NAME               4 (json)

 25           LOAD_SMALL_INT           0
              LOAD_CONST               3 (('dataclass', 'field'))
              IMPORT_NAME              5 (dataclasses)
              IMPORT_FROM              6 (dataclass)
              STORE_NAME               6 (dataclass)
              IMPORT_FROM              7 (field)
              STORE_NAME               7 (field)
              POP_TOP

 26           LOAD_SMALL_INT           0
              LOAD_CONST               4 (('Any', 'Dict', 'List', 'Tuple'))
              IMPORT_NAME              8 (typing)
              IMPORT_FROM              9 (Any)
              STORE_NAME               9 (Any)
              IMPORT_FROM             10 (Dict)
              STORE_NAME              10 (Dict)
              IMPORT_FROM             11 (List)
              STORE_NAME              11 (List)
              IMPORT_FROM             12 (Tuple)
              STORE_NAME              12 (Tuple)
              POP_TOP

 28           LOAD_SMALL_INT           0
              LOAD_CONST               5 (('Polygon',))
              IMPORT_NAME             13 (shapely.geometry)
              IMPORT_FROM             14 (Polygon)
              STORE_NAME              14 (Polygon)
              POP_TOP

 29           LOAD_SMALL_INT           0
              LOAD_CONST               6 (('explain_validity',))
              IMPORT_NAME             15 (shapely.validation)
              IMPORT_FROM             16 (explain_validity)
              STORE_NAME              16 (explain_validity)
              POP_TOP

 32           LOAD_NAME                6 (dataclass)

 33           LOAD_BUILD_CLASS
              PUSH_NULL
              LOAD_CONST               7 (<code object PocketFeasibilityResult at 0x0000024B1C62D790, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 32>)
              MAKE_FUNCTION
              LOAD_CONST               8 ('PocketFeasibilityResult')
              CALL                     2

 32           CALL                     0

 33           STORE_NAME              17 (PocketFeasibilityResult)

 52           LOAD_CONST               9 (<code object __annotate__ at 0x0000024B1C70CF30, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 52>)
              MAKE_FUNCTION
              LOAD_CONST              10 (<code object _points_to_coords at 0x0000024B1C6B1110, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 52>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              18 (_points_to_coords)

 57           LOAD_CONST              11 (<code object __annotate__ at 0x0000024B1C6D1E30, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 57>)
              MAKE_FUNCTION
              LOAD_CONST              12 (<code object _validate_polygon_geometry at 0x0000024B1C67CDC0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 57>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              19 (_validate_polygon_geometry)

 92           LOAD_CONST              13 (<code object __annotate__ at 0x0000024B1C6D1F30, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 92>)
              MAKE_FUNCTION
              LOAD_CONST              14 (<code object _validate_island_within_boundary at 0x0000024B1C40C190, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 92>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              20 (_validate_island_within_boundary)

122           LOAD_CONST              15 (<code object __annotate__ at 0x0000024B1C70D020, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 122>)
              MAKE_FUNCTION
              LOAD_CONST              16 (<code object _validate_islands_non_overlapping at 0x0000024B1C4F5E10, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 122>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              21 (_validate_islands_non_overlapping)

152           LOAD_CONST              17 (<code object __annotate__ at 0x0000024B1C6D2030, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 152>)
              MAKE_FUNCTION
              LOAD_CONST              18 (<code object compute_pocket_area at 0x0000024B1C6852F0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 152>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              22 (compute_pocket_area)

177           LOAD_CONST              19 (<code object __annotate__ at 0x0000024B1C6B1470, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 177>)
              MAKE_FUNCTION
              LOAD_CONST              20 (<code object compute_pocket_feasibility at 0x0000024B1C4F7810, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 177>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              23 (compute_pocket_feasibility)

376           LOAD_CONST              21 (<code object __annotate__ at 0x0000024B1C70D200, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 376>)
              MAKE_FUNCTION
              LOAD_CONST              22 (<code object hash_feasibility_result at 0x0000024B1C6DDAC0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 376>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              24 (hash_feasibility_result)
              LOAD_CONST               2 (None)
              RETURN_VALUE

Disassembly of <code object PocketFeasibilityResult at 0x0000024B1C62D790, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 32>:
 32           RESUME                   0
              LOAD_NAME                0 (__name__)
              STORE_NAME               1 (__module__)
              LOAD_CONST               0 ('PocketFeasibilityResult')
              STORE_NAME               2 (__qualname__)
              LOAD_SMALL_INT          32
              STORE_NAME               3 (__firstlineno__)
              SETUP_ANNOTATIONS

 34           LOAD_CONST               1 ('Result of pocketing feasibility check.')
              STORE_NAME               4 (__doc__)

 36           LOAD_CONST               2 ('bool')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               3 ('feasible')
              STORE_SUBSCR

 37           LOAD_CONST               4 ('str')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               5 ('risk_level')
              STORE_SUBSCR

 38           LOAD_NAME                6 (field)
              PUSH_NULL
              LOAD_NAME                7 (list)
              LOAD_CONST               6 (('default_factory',))
              CALL_KW                  1
              STORE_NAME               8 (issues)
              LOAD_CONST               7 ('List[str]')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               8 ('issues')
              STORE_SUBSCR

 39           LOAD_NAME                6 (field)
              PUSH_NULL
              LOAD_NAME                7 (list)
              LOAD_CONST               6 (('default_factory',))
              CALL_KW                  1
              STORE_NAME               9 (warnings)
              LOAD_CONST               7 ('List[str]')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               9 ('warnings')
              STORE_SUBSCR

 40           LOAD_NAME                6 (field)
              PUSH_NULL
              LOAD_NAME               10 (dict)
              LOAD_CONST               6 (('default_factory',))
              CALL_KW                  1
              STORE_NAME              11 (summary)
              LOAD_CONST              10 ('Dict[str, Any]')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              11 ('summary')
              STORE_SUBSCR

 42           LOAD_CONST              12 (<code object __annotate__ at 0x0000024B1C70CE40, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 42>)
              MAKE_FUNCTION
              LOAD_CONST              13 (<code object to_dict at 0x0000024B1C6278A0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 42>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              12 (to_dict)
              LOAD_CONST              14 (())
              STORE_NAME              13 (__static_attributes__)
              LOAD_CONST              15 (None)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C70CE40, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 42>:
 42           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('return')
              LOAD_CONST               2 ('Dict[str, Any]')
              BUILD_MAP                1
              RETURN_VALUE

Disassembly of <code object to_dict at 0x0000024B1C6278A0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 42>:
 42           RESUME                   0

 44           LOAD_CONST               0 ('feasible')
              LOAD_FAST_BORROW         0 (self)
              LOAD_ATTR                0 (feasible)

 45           LOAD_CONST               1 ('risk_level')
              LOAD_FAST_BORROW         0 (self)
              LOAD_ATTR                2 (risk_level)

 46           LOAD_CONST               2 ('issues')
              LOAD_FAST_BORROW         0 (self)
              LOAD_ATTR                4 (issues)

 47           LOAD_CONST               3 ('warnings')
              LOAD_FAST_BORROW         0 (self)
              LOAD_ATTR                6 (warnings)

 48           LOAD_CONST               4 ('summary')
              LOAD_FAST_BORROW         0 (self)
              LOAD_ATTR                8 (summary)

 43           BUILD_MAP                5
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C70CF30, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 52>:
 52           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('points')
              LOAD_CONST               2 ('List[Tuple[float, float]]')
              LOAD_CONST               3 ('return')
              LOAD_CONST               2 ('List[Tuple[float, float]]')
              BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object _points_to_coords at 0x0000024B1C6B1110, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 52>:
  52           RESUME                   0

  54           LOAD_FAST_BORROW         0 (points)
               GET_ITER
               LOAD_FAST_AND_CLEAR      1 (p)
               SWAP                     2
       L1:     BUILD_LIST               0
               SWAP                     2
       L2:     FOR_ITER                20 (to L3)
               STORE_FAST_LOAD_FAST    17 (p, p)
               LOAD_SMALL_INT           0
               BINARY_OP               26 ([])
               LOAD_FAST_BORROW         1 (p)
               LOAD_SMALL_INT           1
               BINARY_OP               26 ([])
               BUILD_TUPLE              2
               LIST_APPEND              2
               JUMP_BACKWARD           22 (to L2)
       L3:     END_FOR
               POP_ITER
       L4:     SWAP                     2
               STORE_FAST               1 (p)
               RETURN_VALUE

  --   L5:     SWAP                     2
               POP_TOP

  54           SWAP                     2
               STORE_FAST               1 (p)
               RERAISE                  0
ExceptionTable:
  L1 to L4 -> L5 [2]

Disassembly of <code object __annotate__ at 0x0000024B1C6D1E30, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 57>:
 57           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('coords')

 58           LOAD_CONST               2 ('List[Tuple[float, float]]')

 57           LOAD_CONST               3 ('name')

 59           LOAD_CONST               4 ('str')

 57           LOAD_CONST               5 ('return')

 60           LOAD_CONST               6 ('Tuple[bool, str]')

 57           BUILD_MAP                3
              RETURN_VALUE

Disassembly of <code object _validate_polygon_geometry at 0x0000024B1C67CDC0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 57>:
  57            RESUME                   0

  77            LOAD_GLOBAL              1 (len + NULL)
                LOAD_FAST_BORROW         0 (coords)
                CALL                     1
                LOAD_SMALL_INT           3
                COMPARE_OP              18 (bool(<))
                POP_JUMP_IF_FALSE        8 (to L1)
                NOT_TAKEN

  78            LOAD_CONST               1 (False)
                LOAD_FAST_BORROW         1 (name)
                FORMAT_SIMPLE
                LOAD_CONST               2 (' must have at least 3 points')
                BUILD_STRING             2
                BUILD_TUPLE              2
                RETURN_VALUE

  80    L1:     NOP

  81    L2:     LOAD_GLOBAL              3 (Polygon + NULL)
                LOAD_FAST_BORROW         0 (coords)
                CALL                     1
                STORE_FAST               2 (poly)

  82            LOAD_FAST_BORROW         2 (poly)
                LOAD_ATTR                4 (is_valid)
                TO_BOOL
                POP_JUMP_IF_TRUE        21 (to L4)
                NOT_TAKEN

  83            LOAD_GLOBAL              7 (explain_validity + NULL)
                LOAD_FAST_BORROW         2 (poly)
                CALL                     1
                STORE_FAST               3 (reason)

  84            LOAD_CONST               1 (False)
                LOAD_FAST_BORROW         1 (name)
                FORMAT_SIMPLE
                LOAD_CONST               3 (' is not a valid polygon: ')
                LOAD_FAST_BORROW         3 (reason)
                FORMAT_SIMPLE
                BUILD_STRING             3
                BUILD_TUPLE              2
        L3:     RETURN_VALUE

  85    L4:     LOAD_FAST_BORROW         2 (poly)
                LOAD_ATTR                8 (is_empty)
                TO_BOOL
                POP_JUMP_IF_FALSE        8 (to L8)
        L5:     NOT_TAKEN

  86    L6:     LOAD_CONST               1 (False)
                LOAD_FAST_BORROW         1 (name)
                FORMAT_SIMPLE
                LOAD_CONST               4 (' is empty')
                BUILD_STRING             2
                BUILD_TUPLE              2
        L7:     RETURN_VALUE

  87    L8:     LOAD_CONST               7 ((True, ''))
        L9:     RETURN_VALUE

  --   L10:     PUSH_EXC_INFO

  88            LOAD_GLOBAL             10 (Exception)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE       29 (to L15)
                NOT_TAKEN
                STORE_FAST               4 (e)

  89   L11:     LOAD_CONST               1 (False)
                LOAD_FAST                1 (name)
                FORMAT_SIMPLE
                LOAD_CONST               5 (' geometry error: ')
                LOAD_GLOBAL             13 (str + NULL)
                LOAD_FAST                4 (e)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             3
                BUILD_TUPLE              2
       L12:     SWAP                     2
       L13:     POP_EXCEPT
                LOAD_CONST               6 (None)
                STORE_FAST               4 (e)
                DELETE_FAST              4 (e)
                RETURN_VALUE

  --   L14:     LOAD_CONST               6 (None)
                STORE_FAST               4 (e)
                DELETE_FAST              4 (e)
                RERAISE                  1

  88   L15:     RERAISE                  0

  --   L16:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
ExceptionTable:
  L2 to L3 -> L10 [0]
  L4 to L5 -> L10 [0]
  L6 to L7 -> L10 [0]
  L8 to L9 -> L10 [0]
  L10 to L11 -> L16 [1] lasti
  L11 to L12 -> L14 [1] lasti
  L12 to L13 -> L16 [1] lasti
  L14 to L16 -> L16 [1] lasti

Disassembly of <code object __annotate__ at 0x0000024B1C6D1F30, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 92>:
 92           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('boundary_coords')

 93           LOAD_CONST               2 ('List[Tuple[float, float]]')

 92           LOAD_CONST               3 ('island_coords')

 94           LOAD_CONST               2 ('List[Tuple[float, float]]')

 92           LOAD_CONST               4 ('island_index')

 95           LOAD_CONST               5 ('int')

 92           LOAD_CONST               6 ('return')

 96           LOAD_CONST               7 ('Tuple[bool, str]')

 92           BUILD_MAP                4
              RETURN_VALUE

Disassembly of <code object _validate_island_within_boundary at 0x0000024B1C40C190, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 92>:
  92            RESUME                   0

 108            NOP

 109    L1:     LOAD_GLOBAL              1 (Polygon + NULL)
                LOAD_FAST_BORROW         0 (boundary_coords)
                CALL                     1
                STORE_FAST               3 (boundary_poly)

 110            LOAD_GLOBAL              1 (Polygon + NULL)
                LOAD_FAST_BORROW         1 (island_coords)
                CALL                     1
                STORE_FAST               4 (island_poly)

 112            LOAD_FAST_BORROW         3 (boundary_poly)
                LOAD_ATTR                3 (contains + NULL|self)
                LOAD_FAST_BORROW         4 (island_poly)
                CALL                     1
                TO_BOOL
                POP_JUMP_IF_TRUE        63 (to L9)
                NOT_TAKEN

 113            LOAD_FAST_BORROW         3 (boundary_poly)
                LOAD_ATTR                5 (intersects + NULL|self)
                LOAD_FAST_BORROW         4 (island_poly)
                CALL                     1
                TO_BOOL
                POP_JUMP_IF_FALSE       32 (to L7)
        L2:     NOT_TAKEN
        L3:     LOAD_FAST_BORROW         3 (boundary_poly)
                LOAD_ATTR                3 (contains + NULL|self)
                LOAD_FAST_BORROW         4 (island_poly)
                CALL                     1
                TO_BOOL
                POP_JUMP_IF_TRUE         9 (to L7)
        L4:     NOT_TAKEN

 114    L5:     LOAD_CONST               1 (False)
                LOAD_CONST               2 ('island ')
                LOAD_FAST_BORROW         2 (island_index)
                FORMAT_SIMPLE
                LOAD_CONST               3 (' extends outside boundary')
                BUILD_STRING             3
                BUILD_TUPLE              2
        L6:     RETURN_VALUE

 116    L7:     LOAD_CONST               1 (False)
                LOAD_CONST               2 ('island ')
                LOAD_FAST_BORROW         2 (island_index)
                FORMAT_SIMPLE
                LOAD_CONST               4 (' is not within boundary')
                BUILD_STRING             3
                BUILD_TUPLE              2
        L8:     RETURN_VALUE

 117    L9:     LOAD_CONST               7 ((True, ''))
       L10:     RETURN_VALUE

  --   L11:     PUSH_EXC_INFO

 118            LOAD_GLOBAL              6 (Exception)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE       30 (to L16)
                NOT_TAKEN
                STORE_FAST               5 (e)

 119   L12:     LOAD_CONST               1 (False)
                LOAD_CONST               2 ('island ')
                LOAD_FAST                2 (island_index)
                FORMAT_SIMPLE
                LOAD_CONST               5 (' containment check failed: ')
                LOAD_GLOBAL              9 (str + NULL)
                LOAD_FAST                5 (e)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             4
                BUILD_TUPLE              2
       L13:     SWAP                     2
       L14:     POP_EXCEPT
                LOAD_CONST               6 (None)
                STORE_FAST               5 (e)
                DELETE_FAST              5 (e)
                RETURN_VALUE

  --   L15:     LOAD_CONST               6 (None)
                STORE_FAST               5 (e)
                DELETE_FAST              5 (e)
                RERAISE                  1

 118   L16:     RERAISE                  0

  --   L17:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
ExceptionTable:
  L1 to L2 -> L11 [0]
  L3 to L4 -> L11 [0]
  L5 to L6 -> L11 [0]
  L7 to L8 -> L11 [0]
  L9 to L10 -> L11 [0]
  L11 to L12 -> L17 [1] lasti
  L12 to L13 -> L15 [1] lasti
  L13 to L14 -> L17 [1] lasti
  L15 to L17 -> L17 [1] lasti

Disassembly of <code object __annotate__ at 0x0000024B1C70D020, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 122>:
122           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('islands_coords')

123           LOAD_CONST               2 ('List[List[Tuple[float, float]]]')

122           LOAD_CONST               3 ('return')

124           LOAD_CONST               4 ('Tuple[bool, str]')

122           BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object _validate_islands_non_overlapping at 0x0000024B1C4F5E10, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 122>:
 122            RESUME                   0

 134            LOAD_GLOBAL              1 (len + NULL)
                LOAD_FAST_BORROW         0 (islands_coords)
                CALL                     1
                LOAD_SMALL_INT           2
                COMPARE_OP              18 (bool(<))
                POP_JUMP_IF_FALSE        3 (to L1)
                NOT_TAKEN

 135            LOAD_CONST               7 ((True, ''))
                RETURN_VALUE

 137    L1:     NOP

 138    L2:     LOAD_FAST_BORROW         0 (islands_coords)
                GET_ITER
                LOAD_FAST_AND_CLEAR      1 (coords)
                SWAP                     2
        L3:     BUILD_LIST               0
                SWAP                     2
        L4:     FOR_ITER                14 (to L5)
                STORE_FAST               1 (coords)
                LOAD_GLOBAL              3 (Polygon + NULL)
                LOAD_FAST_BORROW         1 (coords)
                CALL                     1
                LIST_APPEND              2
                JUMP_BACKWARD           16 (to L4)
        L5:     END_FOR
                POP_ITER
        L6:     STORE_FAST               2 (island_polys)
                STORE_FAST               1 (coords)

 140            LOAD_GLOBAL              5 (range + NULL)
                LOAD_GLOBAL              1 (len + NULL)
                LOAD_FAST_BORROW         2 (island_polys)
                CALL                     1
                CALL                     1
                GET_ITER
        L7:     FOR_ITER               136 (to L15)
                STORE_FAST               3 (i)

 141            LOAD_GLOBAL              5 (range + NULL)
                LOAD_FAST_BORROW         3 (i)
                LOAD_SMALL_INT           1
                BINARY_OP                0 (+)
                LOAD_GLOBAL              1 (len + NULL)
                LOAD_FAST_BORROW         2 (island_polys)
                CALL                     1
                CALL                     2
                GET_ITER
        L8:     FOR_ITER               101 (to L14)
                STORE_FAST               4 (j)

 142            LOAD_FAST_BORROW_LOAD_FAST_BORROW 35 (island_polys, i)
                BINARY_OP               26 ([])
                LOAD_ATTR                7 (intersects + NULL|self)
                LOAD_FAST_BORROW_LOAD_FAST_BORROW 36 (island_polys, j)
                BINARY_OP               26 ([])
                CALL                     1
                TO_BOOL
        L9:     POP_JUMP_IF_TRUE         3 (to L10)
                NOT_TAKEN
                JUMP_BACKWARD           40 (to L8)

 144   L10:     LOAD_FAST_BORROW_LOAD_FAST_BORROW 35 (island_polys, i)
                BINARY_OP               26 ([])
                LOAD_ATTR                9 (intersection + NULL|self)
                LOAD_FAST_BORROW_LOAD_FAST_BORROW 36 (island_polys, j)
                BINARY_OP               26 ([])
                CALL                     1
                STORE_FAST               5 (intersection)

 145            LOAD_FAST_BORROW         5 (intersection)
                LOAD_ATTR               10 (area)
                LOAD_SMALL_INT           0
                COMPARE_OP             148 (bool(>))
       L11:     POP_JUMP_IF_TRUE         3 (to L12)
                NOT_TAKEN
                JUMP_BACKWARD           88 (to L8)

 146   L12:     LOAD_CONST               1 (False)
                LOAD_CONST               2 ('islands ')
                LOAD_FAST_BORROW         3 (i)
                FORMAT_SIMPLE
                LOAD_CONST               3 (' and ')
                LOAD_FAST_BORROW         4 (j)
                FORMAT_SIMPLE
                LOAD_CONST               4 (' overlap')
                BUILD_STRING             5
                BUILD_TUPLE              2
                SWAP                     2
                POP_TOP
                SWAP                     2
                POP_TOP
       L13:     RETURN_VALUE

 141   L14:     END_FOR
                POP_ITER
                JUMP_BACKWARD          138 (to L7)

 140   L15:     END_FOR
                POP_ITER

 147            LOAD_CONST               7 ((True, ''))
       L16:     RETURN_VALUE

  --   L17:     SWAP                     2
                POP_TOP

 138            SWAP                     2
                STORE_FAST               1 (coords)
                RERAISE                  0

  --   L18:     PUSH_EXC_INFO

 148            LOAD_GLOBAL             12 (Exception)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE       27 (to L23)
                NOT_TAKEN
                STORE_FAST               6 (e)

 149   L19:     LOAD_CONST               1 (False)
                LOAD_CONST               5 ('island overlap check failed: ')
                LOAD_GLOBAL             15 (str + NULL)
                LOAD_FAST                6 (e)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             2
                BUILD_TUPLE              2
       L20:     SWAP                     2
       L21:     POP_EXCEPT
                LOAD_CONST               6 (None)
                STORE_FAST               6 (e)
                DELETE_FAST              6 (e)
                RETURN_VALUE

  --   L22:     LOAD_CONST               6 (None)
                STORE_FAST               6 (e)
                DELETE_FAST              6 (e)
                RERAISE                  1

 148   L23:     RERAISE                  0

  --   L24:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
ExceptionTable:
  L2 to L3 -> L18 [0]
  L3 to L6 -> L17 [2]
  L6 to L9 -> L18 [0]
  L10 to L11 -> L18 [0]
  L12 to L13 -> L18 [0]
  L14 to L16 -> L18 [0]
  L17 to L18 -> L18 [0]
  L18 to L19 -> L24 [1] lasti
  L19 to L20 -> L22 [1] lasti
  L20 to L21 -> L24 [1] lasti
  L22 to L24 -> L24 [1] lasti

Disassembly of <code object __annotate__ at 0x0000024B1C6D2030, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 152>:
152           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('boundary_coords')

153           LOAD_CONST               2 ('List[Tuple[float, float]]')

152           LOAD_CONST               3 ('islands_coords')

154           LOAD_CONST               4 ('List[List[Tuple[float, float]]]')

152           LOAD_CONST               5 ('return')

155           LOAD_CONST               6 ('float')

152           BUILD_MAP                3
              RETURN_VALUE

Disassembly of <code object compute_pocket_area at 0x0000024B1C6852F0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 152>:
152           RESUME                   0

169           LOAD_GLOBAL              1 (Polygon + NULL)
              LOAD_FAST_BORROW         0 (boundary_coords)
              CALL                     1
              STORE_FAST               2 (boundary_poly)

170           LOAD_FAST_BORROW         2 (boundary_poly)
              LOAD_ATTR                2 (area)
              STORE_FAST               3 (boundary_area)

172           LOAD_GLOBAL              5 (sum + NULL)
              LOAD_CONST               1 (<code object <genexpr> at 0x0000024B1C6B1350, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 172>)
              MAKE_FUNCTION
              LOAD_FAST_BORROW         1 (islands_coords)
              GET_ITER
              CALL                     0
              CALL                     1
              STORE_FAST               4 (island_area)

174           LOAD_FAST_BORROW_LOAD_FAST_BORROW 52 (boundary_area, island_area)
              BINARY_OP               10 (-)
              RETURN_VALUE

Disassembly of <code object <genexpr> at 0x0000024B1C6B1350, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 172>:
 172           RETURN_GENERATOR
               POP_TOP
       L1:     RESUME                   0
               LOAD_FAST                0 (.0)
       L2:     FOR_ITER                26 (to L3)
               STORE_FAST               1 (coords)
               LOAD_GLOBAL              1 (Polygon + NULL)
               LOAD_FAST_BORROW         1 (coords)
               CALL                     1
               LOAD_ATTR                2 (area)
               YIELD_VALUE              0
               RESUME                   5
               POP_TOP
               JUMP_BACKWARD           28 (to L2)
       L3:     END_FOR
               POP_ITER
               LOAD_CONST               0 (None)
               RETURN_VALUE

  --   L4:     CALL_INTRINSIC_1         3 (INTRINSIC_STOPITERATION_ERROR)
               RERAISE                  1
ExceptionTable:
  L1 to L4 -> L4 [0] lasti

Disassembly of <code object __annotate__ at 0x0000024B1C6B1470, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 177>:
177           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('boundary')

179           LOAD_CONST               2 ('List[Tuple[float, float]]')

177           LOAD_CONST               3 ('islands')

180           LOAD_CONST               4 ('List[List[Tuple[float, float]]]')

177           LOAD_CONST               5 ('pocket_depth_mm')

181           LOAD_CONST               6 ('float')

177           LOAD_CONST               7 ('tool_diameter_mm')

182           LOAD_CONST               6 ('float')

177           LOAD_CONST               8 ('stepover_percent')

183           LOAD_CONST               6 ('float')

177           LOAD_CONST               9 ('feed_rate_mm_min')

184           LOAD_CONST               6 ('float')

177           LOAD_CONST              10 ('plunge_rate_mm_min')

185           LOAD_CONST               6 ('float')

177           LOAD_CONST              11 ('safe_z_mm')

186           LOAD_CONST               6 ('float')

177           LOAD_CONST              12 ('retract_z_mm')

187           LOAD_CONST               6 ('float')

177           LOAD_CONST              13 ('stepdown_mm')

188           LOAD_CONST               6 ('float')

177           LOAD_CONST              14 ('finish_allowance_mm')

189           LOAD_CONST               6 ('float')

177           LOAD_CONST              15 ('return')

190           LOAD_CONST              16 ('PocketFeasibilityResult')

177           BUILD_MAP               12
              RETURN_VALUE

Disassembly of <code object compute_pocket_feasibility at 0x0000024B1C4F7810, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 177>:
 177            RESUME                   0

 228            BUILD_LIST               0
                STORE_FAST              11 (issues)

 229            BUILD_LIST               0
                STORE_FAST              12 (warnings)

 236            LOAD_GLOBAL              1 (_validate_polygon_geometry + NULL)
                LOAD_FAST_BORROW         0 (boundary)
                LOAD_CONST               1 ('boundary')
                CALL                     2
                UNPACK_SEQUENCE          2
                STORE_FAST_STORE_FAST  222 (valid, error)

 237            LOAD_FAST_BORROW        13 (valid)
                TO_BOOL
                POP_JUMP_IF_TRUE        18 (to L1)
                NOT_TAKEN

 238            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_FAST_BORROW        14 (error)
                CALL                     1
                POP_TOP

 241    L1:     LOAD_GLOBAL              5 (enumerate + NULL)
                LOAD_FAST_BORROW         1 (islands)
                CALL                     1
                GET_ITER
        L2:     FOR_ITER                50 (to L4)
                UNPACK_SEQUENCE          2
                STORE_FAST              15 (i)
                STORE_FAST              16 (island)

 242            LOAD_GLOBAL              1 (_validate_polygon_geometry + NULL)
                LOAD_FAST_BORROW        16 (island)
                LOAD_CONST               2 ('island ')
                LOAD_FAST_BORROW        15 (i)
                FORMAT_SIMPLE
                BUILD_STRING             2
                CALL                     2
                UNPACK_SEQUENCE          2
                STORE_FAST_STORE_FAST  222 (valid, error)

 243            LOAD_FAST_BORROW        13 (valid)
                TO_BOOL
                POP_JUMP_IF_FALSE        3 (to L3)
                NOT_TAKEN
                JUMP_BACKWARD           33 (to L2)

 244    L3:     LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_FAST_BORROW        14 (error)
                CALL                     1
                POP_TOP
                JUMP_BACKWARD           52 (to L2)

 241    L4:     END_FOR
                POP_ITER

 247            LOAD_FAST_BORROW        11 (issues)
                TO_BOOL
                POP_JUMP_IF_TRUE       102 (to L8)
                NOT_TAKEN

 249            LOAD_GLOBAL              5 (enumerate + NULL)
                LOAD_FAST_BORROW         1 (islands)
                CALL                     1
                GET_ITER
        L5:     FOR_ITER                48 (to L7)
                UNPACK_SEQUENCE          2
                STORE_FAST              15 (i)
                STORE_FAST              16 (island)

 250            LOAD_GLOBAL              7 (_validate_island_within_boundary + NULL)
                LOAD_FAST_BORROW         0 (boundary)
                LOAD_FAST_BORROW        16 (island)
                LOAD_FAST_BORROW        15 (i)
                CALL                     3
                UNPACK_SEQUENCE          2
                STORE_FAST_STORE_FAST  222 (valid, error)

 251            LOAD_FAST_BORROW        13 (valid)
                TO_BOOL
                POP_JUMP_IF_FALSE        3 (to L6)
                NOT_TAKEN
                JUMP_BACKWARD           31 (to L5)

 252    L6:     LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_FAST_BORROW        14 (error)
                CALL                     1
                POP_TOP
                JUMP_BACKWARD           50 (to L5)

 249    L7:     END_FOR
                POP_ITER

 255            LOAD_GLOBAL              9 (_validate_islands_non_overlapping + NULL)
                LOAD_FAST_BORROW         1 (islands)
                CALL                     1
                UNPACK_SEQUENCE          2
                STORE_FAST_STORE_FAST  222 (valid, error)

 256            LOAD_FAST_BORROW        13 (valid)
                TO_BOOL
                POP_JUMP_IF_TRUE        18 (to L8)
                NOT_TAKEN

 257            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_FAST_BORROW        14 (error)
                CALL                     1
                POP_TOP

 264    L8:     LOAD_FAST_BORROW         3 (tool_diameter_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP              58 (bool(<=))
                POP_JUMP_IF_FALSE       19 (to L9)
                NOT_TAKEN

 265            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST               3 ('tool_diameter_mm must be > 0')
                CALL                     1
                POP_TOP
                JUMP_FORWARD            57 (to L11)

 266    L9:     LOAD_FAST_BORROW         3 (tool_diameter_mm)
                LOAD_CONST               4 (0.5)
                COMPARE_OP              18 (bool(<))
                POP_JUMP_IF_FALSE       23 (to L10)
                NOT_TAKEN

 267            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST               5 ('tool_diameter_mm=')
                LOAD_FAST_BORROW         3 (tool_diameter_mm)
                FORMAT_SIMPLE
                LOAD_CONST               6 ('mm below L.1 minimum (0.5mm)')
                BUILD_STRING             3
                CALL                     1
                POP_TOP
                JUMP_FORWARD            28 (to L11)

 268   L10:     LOAD_FAST_BORROW         3 (tool_diameter_mm)
                LOAD_CONST               7 (50.0)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       22 (to L11)
                NOT_TAKEN

 269            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST               5 ('tool_diameter_mm=')
                LOAD_FAST_BORROW         3 (tool_diameter_mm)
                FORMAT_SIMPLE
                LOAD_CONST               8 ('mm above L.1 maximum (50mm)')
                BUILD_STRING             3
                CALL                     1
                POP_TOP

 272   L11:     LOAD_FAST_BORROW         4 (stepover_percent)
                LOAD_CONST               9 (100.0)
                BINARY_OP               11 (/)
                STORE_FAST              17 (stepover_fraction)

 273            LOAD_FAST_BORROW        17 (stepover_fraction)
                LOAD_CONST              10 (0.3)
                COMPARE_OP              18 (bool(<))
                POP_JUMP_IF_FALSE       23 (to L12)
                NOT_TAKEN

 274            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              11 ('stepover_percent=')
                LOAD_FAST_BORROW         4 (stepover_percent)
                FORMAT_SIMPLE
                LOAD_CONST              12 ('% below L.1 minimum (30%)')
                BUILD_STRING             3
                CALL                     1
                POP_TOP
                JUMP_FORWARD            57 (to L14)

 275   L12:     LOAD_FAST_BORROW        17 (stepover_fraction)
                LOAD_CONST              13 (0.7)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       23 (to L13)
                NOT_TAKEN

 276            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              11 ('stepover_percent=')
                LOAD_FAST_BORROW         4 (stepover_percent)
                FORMAT_SIMPLE
                LOAD_CONST              14 ('% above L.1 maximum (70%)')
                BUILD_STRING             3
                CALL                     1
                POP_TOP
                JUMP_FORWARD            28 (to L14)

 277   L13:     LOAD_FAST_BORROW        17 (stepover_fraction)
                LOAD_CONST              15 (0.6)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       22 (to L14)
                NOT_TAKEN

 278            LOAD_FAST_BORROW        12 (warnings)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              11 ('stepover_percent=')
                LOAD_FAST_BORROW         4 (stepover_percent)
                FORMAT_SIMPLE
                LOAD_CONST              16 ('% is aggressive - may leave scallops')
                BUILD_STRING             3
                CALL                     1
                POP_TOP

 281   L14:     LOAD_FAST_BORROW         2 (pocket_depth_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP              58 (bool(<=))
                POP_JUMP_IF_FALSE       19 (to L15)
                NOT_TAKEN

 282            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              17 ('pocket_depth_mm must be > 0')
                CALL                     1
                POP_TOP
                JUMP_FORWARD            28 (to L16)

 283   L15:     LOAD_FAST_BORROW         2 (pocket_depth_mm)
                LOAD_CONST              18 (75.0)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       22 (to L16)
                NOT_TAKEN

 284            LOAD_FAST_BORROW        12 (warnings)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              19 ('pocket_depth_mm=')
                LOAD_FAST_BORROW         2 (pocket_depth_mm)
                FORMAT_SIMPLE
                LOAD_CONST              20 ('mm is very deep')
                BUILD_STRING             3
                CALL                     1
                POP_TOP

 287   L16:     LOAD_FAST_BORROW         9 (stepdown_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP              58 (bool(<=))
                POP_JUMP_IF_FALSE       19 (to L17)
                NOT_TAKEN

 288            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              21 ('stepdown_mm must be > 0')
                CALL                     1
                POP_TOP
                JUMP_FORWARD            27 (to L18)

 289   L17:     LOAD_FAST_BORROW_LOAD_FAST_BORROW 147 (stepdown_mm, tool_diameter_mm)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       22 (to L18)
                NOT_TAKEN

 290            LOAD_FAST_BORROW        12 (warnings)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              22 ('stepdown_mm=')
                LOAD_FAST_BORROW         9 (stepdown_mm)
                FORMAT_SIMPLE
                LOAD_CONST              23 ('mm exceeds tool diameter - aggressive')
                BUILD_STRING             3
                CALL                     1
                POP_TOP

 293   L18:     LOAD_FAST_BORROW         5 (feed_rate_mm_min)
                LOAD_SMALL_INT           0
                COMPARE_OP              58 (bool(<=))
                POP_JUMP_IF_FALSE       18 (to L19)
                NOT_TAKEN

 294            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              24 ('feed_rate_mm_min must be > 0')
                CALL                     1
                POP_TOP

 295   L19:     LOAD_FAST_BORROW         6 (plunge_rate_mm_min)
                LOAD_SMALL_INT           0
                COMPARE_OP              58 (bool(<=))
                POP_JUMP_IF_FALSE       19 (to L20)
                NOT_TAKEN

 296            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              25 ('plunge_rate_mm_min must be > 0')
                CALL                     1
                POP_TOP
                JUMP_FORWARD            23 (to L21)

 297   L20:     LOAD_FAST_BORROW_LOAD_FAST_BORROW 101 (plunge_rate_mm_min, feed_rate_mm_min)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       18 (to L21)
                NOT_TAKEN

 298            LOAD_FAST_BORROW        12 (warnings)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              26 ('plunge_rate exceeds feed_rate - unusual')
                CALL                     1
                POP_TOP

 301   L21:     LOAD_FAST_BORROW         7 (safe_z_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP              58 (bool(<=))
                POP_JUMP_IF_FALSE       18 (to L22)
                NOT_TAKEN

 302            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              27 ('safe_z_mm must be > 0')
                CALL                     1
                POP_TOP

 303   L22:     LOAD_FAST_BORROW         8 (retract_z_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP              58 (bool(<=))
                POP_JUMP_IF_FALSE       18 (to L23)
                NOT_TAKEN

 304            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              28 ('retract_z_mm must be > 0')
                CALL                     1
                POP_TOP

 305   L23:     LOAD_FAST_BORROW_LOAD_FAST_BORROW 135 (retract_z_mm, safe_z_mm)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       18 (to L24)
                NOT_TAKEN

 306            LOAD_FAST_BORROW        12 (warnings)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              29 ('retract_z_mm > safe_z_mm - will use safe_z')
                CALL                     1
                POP_TOP

 309   L24:     LOAD_FAST_BORROW        10 (finish_allowance_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP              18 (bool(<))
                POP_JUMP_IF_FALSE       19 (to L25)
                NOT_TAKEN

 310            LOAD_FAST_BORROW        11 (issues)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              30 ('finish_allowance_mm must be >= 0')
                CALL                     1
                POP_TOP
                JUMP_FORWARD            30 (to L26)

 311   L25:     LOAD_FAST_BORROW_LOAD_FAST_BORROW 163 (finish_allowance_mm, tool_diameter_mm)
                LOAD_SMALL_INT           2
                BINARY_OP               11 (/)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       18 (to L26)
                NOT_TAKEN

 312            LOAD_FAST_BORROW        12 (warnings)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              31 ('finish_allowance exceeds tool radius')
                CALL                     1
                POP_TOP

 319   L26:     LOAD_FAST_BORROW         3 (tool_diameter_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       45 (to L27)
                NOT_TAKEN
                LOAD_FAST_BORROW         2 (pocket_depth_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       38 (to L27)
                NOT_TAKEN

 320            LOAD_FAST_BORROW_LOAD_FAST_BORROW 35 (pocket_depth_mm, tool_diameter_mm)
                BINARY_OP               11 (/)
                STORE_FAST              18 (depth_ratio)

 321            LOAD_FAST_BORROW        18 (depth_ratio)
                LOAD_SMALL_INT           3
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       23 (to L27)
                NOT_TAKEN

 322            LOAD_FAST_BORROW        12 (warnings)
                LOAD_ATTR                3 (append + NULL|self)

 323            LOAD_CONST              32 ('Deep pocket: depth/diameter ratio is ')
                LOAD_FAST_BORROW        18 (depth_ratio)
                LOAD_CONST              33 ('.1f')
                FORMAT_WITH_SPEC
                LOAD_CONST              34 ('. Verify tool flute length and chip evacuation.')
                BUILD_STRING             3

 322            CALL                     1
                POP_TOP

 328   L27:     LOAD_FAST_BORROW         9 (stepdown_mm)
                LOAD_SMALL_INT           0
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       71 (to L29)
                NOT_TAKEN

 329            LOAD_GLOBAL             11 (max + NULL)
                LOAD_SMALL_INT           1
                LOAD_GLOBAL             13 (int + NULL)
                LOAD_FAST_BORROW_LOAD_FAST_BORROW 41 (pocket_depth_mm, stepdown_mm)
                BINARY_OP                0 (+)
                LOAD_CONST              35 (0.001)
                BINARY_OP               10 (-)
                LOAD_FAST_BORROW         9 (stepdown_mm)
                BINARY_OP               11 (/)
                CALL                     1
                CALL                     2
                STORE_FAST              19 (pass_count)

 330            LOAD_FAST_BORROW        19 (pass_count)
                LOAD_SMALL_INT          30
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       22 (to L28)
                NOT_TAKEN

 331            LOAD_FAST_BORROW        12 (warnings)
                LOAD_ATTR                3 (append + NULL|self)
                LOAD_CONST              36 ('Estimated ')
                LOAD_FAST_BORROW        19 (pass_count)
                FORMAT_SIMPLE
                LOAD_CONST              37 (' passes - consider larger stepdown')
                BUILD_STRING             3
                CALL                     1
                POP_TOP

  --   L28:     JUMP_FORWARD             2 (to L30)

 333   L29:     LOAD_SMALL_INT           1
                STORE_FAST              19 (pass_count)

 339   L30:     LOAD_FAST_BORROW        11 (issues)
                TO_BOOL
                POP_JUMP_IF_TRUE        13 (to L31)
                NOT_TAKEN

 340            LOAD_GLOBAL             15 (compute_pocket_area + NULL)
                LOAD_FAST_BORROW_LOAD_FAST_BORROW 1 (boundary, islands)
                CALL                     2
                STORE_FAST              20 (pocket_area)
                JUMP_FORWARD             2 (to L32)

 342   L31:     LOAD_CONST              38 (0.0)
                STORE_FAST              20 (pocket_area)

 345   L32:     LOAD_FAST_BORROW        11 (issues)
                TO_BOOL
                POP_JUMP_IF_FALSE        6 (to L33)
                NOT_TAKEN

 346            LOAD_CONST              39 ('blocked')
                STORE_FAST              21 (risk_level)

 347            LOAD_CONST              40 (False)
                STORE_FAST              22 (feasible)
                JUMP_FORWARD            38 (to L36)

 348   L33:     LOAD_GLOBAL             17 (len + NULL)
                LOAD_FAST_BORROW        12 (warnings)
                CALL                     1
                LOAD_SMALL_INT           3
                COMPARE_OP             188 (bool(>=))
                POP_JUMP_IF_FALSE        6 (to L34)
                NOT_TAKEN

 349            LOAD_CONST              41 ('high')
                STORE_FAST              21 (risk_level)

 350            LOAD_CONST              42 (True)
                STORE_FAST              22 (feasible)
                JUMP_FORWARD            17 (to L36)

 351   L34:     LOAD_FAST_BORROW        12 (warnings)
                TO_BOOL
                POP_JUMP_IF_FALSE        6 (to L35)
                NOT_TAKEN

 352            LOAD_CONST              43 ('medium')
                STORE_FAST              21 (risk_level)

 353            LOAD_CONST              42 (True)
                STORE_FAST              22 (feasible)
                JUMP_FORWARD             4 (to L36)

 355   L35:     LOAD_CONST              44 ('low')
                STORE_FAST              21 (risk_level)

 356            LOAD_CONST              42 (True)
                STORE_FAST              22 (feasible)

 359   L36:     LOAD_CONST              45 ('pocket_area_mm2')
                LOAD_GLOBAL             19 (round + NULL)
                LOAD_FAST_BORROW        20 (pocket_area)
                LOAD_SMALL_INT           2
                CALL                     2

 360            LOAD_CONST              46 ('island_count')
                LOAD_GLOBAL             17 (len + NULL)
                LOAD_FAST_BORROW         1 (islands)
                CALL                     1

 361            LOAD_CONST              47 ('estimated_pass_count')
                LOAD_FAST_BORROW        19 (pass_count)

 362            LOAD_CONST              48 ('tool_diameter_mm')
                LOAD_FAST_BORROW         3 (tool_diameter_mm)

 363            LOAD_CONST              49 ('stepover_percent')
                LOAD_FAST_BORROW         4 (stepover_percent)

 364            LOAD_CONST              50 ('pocket_depth_mm')
                LOAD_FAST_BORROW         2 (pocket_depth_mm)

 358            BUILD_MAP                6
                STORE_FAST              23 (summary)

 367            LOAD_GLOBAL             21 (PocketFeasibilityResult + NULL)

 368            LOAD_FAST_BORROW        22 (feasible)

 369            LOAD_FAST_BORROW        21 (risk_level)

 370            LOAD_FAST_BORROW        11 (issues)

 371            LOAD_FAST_BORROW        12 (warnings)

 372            LOAD_FAST_BORROW        23 (summary)

 367            LOAD_CONST              51 (('feasible', 'risk_level', 'issues', 'warnings', 'summary'))
                CALL_KW                  5
                RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C70D200, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 376>:
376           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('result')
              LOAD_CONST               2 ('PocketFeasibilityResult')
              LOAD_CONST               3 ('return')
              LOAD_CONST               4 ('str')
              BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object hash_feasibility_result at 0x0000024B1C6DDAC0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\feasibility.py", line 376>:
376           RESUME                   0

378           LOAD_GLOBAL              0 (json)
              LOAD_ATTR                2 (dumps)
              PUSH_NULL
              LOAD_FAST_BORROW         0 (result)
              LOAD_ATTR                5 (to_dict + NULL|self)
              CALL                     0
              LOAD_CONST               1 (True)
              LOAD_CONST               2 (('sort_keys',))
              CALL_KW                  2
              STORE_FAST               1 (data)

379           LOAD_GLOBAL              6 (hashlib)
              LOAD_ATTR                8 (sha256)
              PUSH_NULL
              LOAD_FAST_BORROW         1 (data)
              LOAD_ATTR               11 (encode + NULL|self)
              CALL                     0
              CALL                     1
              LOAD_ATTR               13 (hexdigest + NULL|self)
              CALL                     0
              RETURN_VALUE

```
---

## `cam/pocketing/intent_adapter`  
`app/cam/pocketing/__pycache__/intent_adapter.cpython-314.pyc` — 8287 bytes, mtime(UTC) 2026-05-25T19:11:45.135797

### Recovered structure (names + string constants)
```
<<module>> names=['__doc__', '__future__', 'annotations', 'dataclasses', 'dataclass', 'field', 'typing', 'Any', 'Dict', 'List', 'Literal', 'Tuple', 'app.rmos.cam.schemas_intent', 'CamIntentV1', 'intent_schema', 'PocketDesignV1', 'validate_pocket_design', 'PocketIntentAdaptation', '_extract_context_float', '_extract_context_str', '_design_points_to_tuples', 'pocket_params_from_intent']
  str: 'PocketIntentAdaptation'
  str: 'default'
  str: 'ge'
  str: 'le'
  str: 'allowed'
  <PocketIntentAdaptation> names=['__name__', '__module__', '__qualname__', '__firstlineno__', '__doc__', '__annotations__', 'field', 'list', 'issues', '__static_attributes__']
    str: 'PocketIntentAdaptation'
    str: 'List[List[Tuple[float, float]]]'
    str: 'loops'
    str: 'float'
    str: 'tool_d'
    str: 'stepover'
    str: 'stepdown'
    str: 'margin'
    str: "Literal['Spiral', 'Lanes']"
    str: 'strategy'
    str: 'smoothing_radius'
    str: 'feed_xy'
    str: 'plunge_rate'
    str: 'safe_z'
    str: 'retract_z'
    str: 'pocket_depth_mm'
    str: 'bool'
    str: 'finish_pass'
    str: 'finish_allowance_mm'
    str: 'List[Dict[str, str]]'
    str: 'issues'
  <__annotate__> names=[]
    str: 'context'
    str: 'Dict[str, Any]'
    str: 'key'
    str: 'str'
    str: 'default'
    str: 'float | None'
    str: 'ge'
    str: 'le'
    str: 'return'
  <_extract_context_float> names=['get', 'float', 'ValueError', 'TypeError', 'type', '__name__']
    str: 'context.'
    str: ' must be a number, got '
    str: ' must be >= '
    str: ', got '
    str: ' must be <= '
  <__annotate__> names=[]
    str: 'context'
    str: 'Dict[str, Any]'
    str: 'key'
    str: 'str'
    str: 'default'
    str: 'str | None'
    str: 'allowed'
    str: 'List[str] | None'
    str: 'return'
  <_extract_context_str> names=['get', 'str', 'ValueError']
    str: 'context.'
    str: ' must be one of '
    str: ', got '
  <__annotate__> names=[]
    str: 'points'
    str: 'List[Any]'
    str: 'return'
    str: 'List[Tuple[float, float]]'
  <_design_points_to_tuples> names=['x', 'y']
    str: 'Convert PocketPointV1 list to coordinate tuples for L.1.'
  <__annotate__> names=[]
    str: 'intent'
    str: 'CamIntentV1'
    str: 'return'
    str: 'PocketIntentAdaptation'
  <pocket_params_from_intent> names=['validate_pocket_design', 'design', '_design_points_to_tuples', 'boundary', 'islands', 'context', 'stepover_percent', '_extract_context_float', '_extract_context_str', 'PocketIntentAdaptation', 'tool_diameter_mm', 'pocket_depth_mm', 'finish_pass', 'finish_allowance_mm']
    str: 'stepdown_mm'
    str: 'margin_mm'
    str: 'strategy'
    str: 'Spiral'
    str: 'Lanes'
    str: 'smoothing_radius_mm'
    str: 'feed_rate_mm_min'
    str: 'plunge_rate_mm_min'
    str: 'safe_z_mm'
    str: 'retract_z_mm'
```

### Full disassembly (`dis.dis`)
```
  0           RESUME                   0

  1           LOAD_CONST               0 ('\nPocketing Intent Adapter\n\nBridge between CamIntentV1 and the L.1 adaptive pocketing engine.\n\nThis adapter maps directly to L.1\'s plan_adaptive_l1 function parameters,\nnot to a PocketConfig dataclass (which doesn\'t exist).\n\nL.1 function signature:\n    plan_adaptive_l1(\n        loops: List[List[Tuple[float, float]]],  # [boundary, *islands]\n        tool_d: float,\n        stepover: float,  # fraction 0.3-0.7\n        stepdown: float,\n        margin: float,\n        strategy: Literal["Spiral", "Lanes"],\n        smoothing_radius: float,\n    ) -> List[Tuple[float, float]]\n\nField mapping:\n- design.boundary -> loops[0]\n- design.islands -> loops[1:]\n- design.tool_diameter_mm -> tool_d\n- design.stepover_percent / 100 -> stepover (fraction)\n- context.stepdown_mm -> stepdown\n- context.margin_mm -> margin\n- context.strategy -> strategy\n- context.smoothing_radius_mm -> smoothing_radius\n\nFollows the wood-data ValueError discipline: raises structured errors\non missing required keys, never falls back to silent defaults.\n')
              STORE_NAME               0 (__doc__)

 33           LOAD_SMALL_INT           0
              LOAD_CONST               1 (('annotations',))
              IMPORT_NAME              1 (__future__)
              IMPORT_FROM              2 (annotations)
              STORE_NAME               2 (annotations)
              POP_TOP

 35           LOAD_SMALL_INT           0
              LOAD_CONST               2 (('dataclass', 'field'))
              IMPORT_NAME              3 (dataclasses)
              IMPORT_FROM              4 (dataclass)
              STORE_NAME               4 (dataclass)
              IMPORT_FROM              5 (field)
              STORE_NAME               5 (field)
              POP_TOP

 36           LOAD_SMALL_INT           0
              LOAD_CONST               3 (('Any', 'Dict', 'List', 'Literal', 'Tuple'))
              IMPORT_NAME              6 (typing)
              IMPORT_FROM              7 (Any)
              STORE_NAME               7 (Any)
              IMPORT_FROM              8 (Dict)
              STORE_NAME               8 (Dict)
              IMPORT_FROM              9 (List)
              STORE_NAME               9 (List)
              IMPORT_FROM             10 (Literal)
              STORE_NAME              10 (Literal)
              IMPORT_FROM             11 (Tuple)
              STORE_NAME              11 (Tuple)
              POP_TOP

 38           LOAD_SMALL_INT           0
              LOAD_CONST               4 (('CamIntentV1',))
              IMPORT_NAME             12 (app.rmos.cam.schemas_intent)
              IMPORT_FROM             13 (CamIntentV1)
              STORE_NAME              13 (CamIntentV1)
              POP_TOP

 40           LOAD_SMALL_INT           1
              LOAD_CONST               5 (('PocketDesignV1', 'validate_pocket_design'))
              IMPORT_NAME             14 (intent_schema)
              IMPORT_FROM             15 (PocketDesignV1)
              STORE_NAME              15 (PocketDesignV1)
              IMPORT_FROM             16 (validate_pocket_design)
              STORE_NAME              16 (validate_pocket_design)
              POP_TOP

 43           LOAD_NAME                4 (dataclass)

 44           LOAD_BUILD_CLASS
              PUSH_NULL
              LOAD_CONST               6 (<code object PocketIntentAdaptation at 0x0000024B1C60A0B0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 43>)
              MAKE_FUNCTION
              LOAD_CONST               7 ('PocketIntentAdaptation')
              CALL                     2

 43           CALL                     0

 44           STORE_NAME              17 (PocketIntentAdaptation)

 78           LOAD_CONST               8 ('default')

 82           LOAD_CONST               9 (None)

 78           LOAD_CONST              10 ('ge')

 83           LOAD_CONST               9 (None)

 78           LOAD_CONST              11 ('le')

 84           LOAD_CONST               9 (None)

 78           BUILD_MAP                3
              LOAD_CONST              12 (<code object __annotate__ at 0x0000024B1C6D2330, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 78>)
              MAKE_FUNCTION
              LOAD_CONST              13 (<code object _extract_context_float at 0x0000024B1C3EF6F0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 78>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              SET_FUNCTION_ATTRIBUTE   2 (kwdefaults)
              STORE_NAME              18 (_extract_context_float)

109           LOAD_CONST               8 ('default')

113           LOAD_CONST               9 (None)

109           LOAD_CONST              14 ('allowed')

114           LOAD_CONST               9 (None)

109           BUILD_MAP                2
              LOAD_CONST              15 (<code object __annotate__ at 0x0000024B1C6D2430, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 109>)
              MAKE_FUNCTION
              LOAD_CONST              16 (<code object _extract_context_str at 0x0000024B1C62DA50, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 109>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              SET_FUNCTION_ATTRIBUTE   2 (kwdefaults)
              STORE_NAME              19 (_extract_context_str)

133           LOAD_CONST              17 (<code object __annotate__ at 0x0000024B1C70CC60, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 133>)
              MAKE_FUNCTION
              LOAD_CONST              18 (<code object _design_points_to_tuples at 0x0000024B1C63EFB0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 133>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              20 (_design_points_to_tuples)

140           LOAD_CONST              19 (<code object __annotate__ at 0x0000024B1C70D2F0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 140>)
              MAKE_FUNCTION
              LOAD_CONST              20 (<code object pocket_params_from_intent at 0x0000024B1C4F8060, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 140>)
              MAKE_FUNCTION
              SET_FUNCTION_ATTRIBUTE  16 (annotate)
              STORE_NAME              21 (pocket_params_from_intent)
              LOAD_CONST               9 (None)
              RETURN_VALUE

Disassembly of <code object PocketIntentAdaptation at 0x0000024B1C60A0B0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 43>:
 43           RESUME                   0
              LOAD_NAME                0 (__name__)
              STORE_NAME               1 (__module__)
              LOAD_CONST               0 ('PocketIntentAdaptation')
              STORE_NAME               2 (__qualname__)
              LOAD_SMALL_INT          43
              STORE_NAME               3 (__firstlineno__)
              SETUP_ANNOTATIONS

 45           LOAD_CONST               1 ("\nAdaptation result mapping CamIntentV1 to L.1 parameters.\n\nThis is NOT a PocketConfig (which doesn't exist) - it's a direct\nmapping to L.1's plan_adaptive_l1 function parameters.\n")
              STORE_NAME               4 (__doc__)

 53           LOAD_CONST               2 ('List[List[Tuple[float, float]]]')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               3 ('loops')
              STORE_SUBSCR

 56           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               5 ('tool_d')
              STORE_SUBSCR

 57           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               6 ('stepover')
              STORE_SUBSCR

 58           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               7 ('stepdown')
              STORE_SUBSCR

 59           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               8 ('margin')
              STORE_SUBSCR

 60           LOAD_CONST               9 ("Literal['Spiral', 'Lanes']")
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              10 ('strategy')
              STORE_SUBSCR

 61           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              11 ('smoothing_radius')
              STORE_SUBSCR

 64           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              12 ('feed_xy')
              STORE_SUBSCR

 65           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              13 ('plunge_rate')
              STORE_SUBSCR

 66           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              14 ('safe_z')
              STORE_SUBSCR

 67           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              15 ('retract_z')
              STORE_SUBSCR

 70           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              16 ('pocket_depth_mm')
              STORE_SUBSCR

 71           LOAD_CONST              17 ('bool')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              18 ('finish_pass')
              STORE_SUBSCR

 72           LOAD_CONST               4 ('float')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              19 ('finish_allowance_mm')
              STORE_SUBSCR

 75           LOAD_NAME                6 (field)
              PUSH_NULL
              LOAD_NAME                7 (list)
              LOAD_CONST              20 (('default_factory',))
              CALL_KW                  1
              STORE_NAME               8 (issues)
              LOAD_CONST              21 ('List[Dict[str, str]]')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST              22 ('issues')
              STORE_SUBSCR
              LOAD_CONST              23 (())
              STORE_NAME               9 (__static_attributes__)
              LOAD_CONST              24 (None)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C6D2330, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 78>:
 78           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('context')

 79           LOAD_CONST               2 ('Dict[str, Any]')

 78           LOAD_CONST               3 ('key')

 80           LOAD_CONST               4 ('str')

 78           LOAD_CONST               5 ('default')

 82           LOAD_CONST               6 ('float | None')

 78           LOAD_CONST               7 ('ge')

 83           LOAD_CONST               6 ('float | None')

 78           LOAD_CONST               8 ('le')

 84           LOAD_CONST               6 ('float | None')

 78           LOAD_CONST               9 ('return')

 85           LOAD_CONST               6 ('float | None')

 78           BUILD_MAP                6
              RETURN_VALUE

Disassembly of <code object _extract_context_float at 0x0000024B1C3EF6F0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 78>:
  78            RESUME                   0

  92            LOAD_FAST_BORROW         0 (context)
                LOAD_ATTR                1 (get + NULL|self)
                LOAD_FAST_BORROW         1 (key)
                CALL                     1
                STORE_FAST               5 (value)

  93            LOAD_FAST_BORROW         5 (value)
                POP_JUMP_IF_NOT_NONE     3 (to L1)
                NOT_TAKEN

  94            LOAD_FAST_BORROW         2 (default)
                RETURN_VALUE

  96    L1:     NOP

  97    L2:     LOAD_GLOBAL              3 (float + NULL)
                LOAD_FAST_BORROW         5 (value)
                CALL                     1
                STORE_FAST               6 (f)

 101    L3:     LOAD_FAST                3 (ge)
                POP_JUMP_IF_NONE        27 (to L4)
                NOT_TAKEN
                LOAD_FAST_LOAD_FAST     99 (f, ge)
                COMPARE_OP              18 (bool(<))
                POP_JUMP_IF_FALSE       21 (to L4)
                NOT_TAKEN

 102            LOAD_GLOBAL              5 (ValueError + NULL)
                LOAD_CONST               2 ('context.')
                LOAD_FAST                1 (key)
                FORMAT_SIMPLE
                LOAD_CONST               4 (' must be >= ')
                LOAD_FAST                3 (ge)
                FORMAT_SIMPLE
                LOAD_CONST               5 (', got ')
                LOAD_FAST                6 (f)
                FORMAT_SIMPLE
                BUILD_STRING             6
                CALL                     1
                RAISE_VARARGS            1

 103    L4:     LOAD_FAST                4 (le)
                POP_JUMP_IF_NONE        27 (to L5)
                NOT_TAKEN
                LOAD_FAST_LOAD_FAST    100 (f, le)
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       21 (to L5)
                NOT_TAKEN

 104            LOAD_GLOBAL              5 (ValueError + NULL)
                LOAD_CONST               2 ('context.')
                LOAD_FAST                1 (key)
                FORMAT_SIMPLE
                LOAD_CONST               6 (' must be <= ')
                LOAD_FAST                4 (le)
                FORMAT_SIMPLE
                LOAD_CONST               5 (', got ')
                LOAD_FAST                6 (f)
                FORMAT_SIMPLE
                BUILD_STRING             6
                CALL                     1
                RAISE_VARARGS            1

 106    L5:     LOAD_FAST                6 (f)
                RETURN_VALUE

  --    L6:     PUSH_EXC_INFO

  98            LOAD_GLOBAL              4 (ValueError)
                LOAD_GLOBAL              6 (TypeError)
                BUILD_TUPLE              2
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE       43 (to L9)
                NOT_TAKEN
                STORE_FAST               7 (e)

  99    L7:     LOAD_GLOBAL              5 (ValueError + NULL)
                LOAD_CONST               2 ('context.')
                LOAD_FAST                1 (key)
                FORMAT_SIMPLE
                LOAD_CONST               3 (' must be a number, got ')
                LOAD_GLOBAL              9 (type + NULL)
                LOAD_FAST                5 (value)
                CALL                     1
                LOAD_ATTR               10 (__name__)
                FORMAT_SIMPLE
                BUILD_STRING             4
                CALL                     1
                LOAD_FAST                7 (e)
                RAISE_VARARGS            2

  --    L8:     LOAD_CONST               1 (None)
                STORE_FAST               7 (e)
                DELETE_FAST              7 (e)
                RERAISE                  1

  98    L9:     RERAISE                  0

  --   L10:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
ExceptionTable:
  L2 to L3 -> L6 [0]
  L6 to L7 -> L10 [1] lasti
  L7 to L8 -> L8 [1] lasti
  L8 to L10 -> L10 [1] lasti

Disassembly of <code object __annotate__ at 0x0000024B1C6D2430, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 109>:
109           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('context')

110           LOAD_CONST               2 ('Dict[str, Any]')

109           LOAD_CONST               3 ('key')

111           LOAD_CONST               4 ('str')

109           LOAD_CONST               5 ('default')

113           LOAD_CONST               6 ('str | None')

109           LOAD_CONST               7 ('allowed')

114           LOAD_CONST               8 ('List[str] | None')

109           LOAD_CONST               9 ('return')

115           LOAD_CONST               6 ('str | None')

109           BUILD_MAP                5
              RETURN_VALUE

Disassembly of <code object _extract_context_str at 0x0000024B1C62DA50, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 109>:
109           RESUME                   0

122           LOAD_FAST_BORROW         0 (context)
              LOAD_ATTR                1 (get + NULL|self)
              LOAD_FAST_BORROW         1 (key)
              CALL                     1
              STORE_FAST               4 (value)

123           LOAD_FAST_BORROW         4 (value)
              POP_JUMP_IF_NOT_NONE     3 (to L1)
              NOT_TAKEN

124           LOAD_FAST_BORROW         2 (default)
              RETURN_VALUE

126   L1:     LOAD_GLOBAL              3 (str + NULL)
              LOAD_FAST_BORROW         4 (value)
              CALL                     1
              STORE_FAST               5 (s)

127           LOAD_FAST_BORROW         3 (allowed)
              POP_JUMP_IF_NONE        27 (to L2)
              NOT_TAKEN
              LOAD_FAST_BORROW_LOAD_FAST_BORROW 83 (s, allowed)
              CONTAINS_OP              1 (not in)
              POP_JUMP_IF_FALSE       21 (to L2)
              NOT_TAKEN

128           LOAD_GLOBAL              5 (ValueError + NULL)
              LOAD_CONST               1 ('context.')
              LOAD_FAST_BORROW         1 (key)
              FORMAT_SIMPLE
              LOAD_CONST               2 (' must be one of ')
              LOAD_FAST_BORROW         3 (allowed)
              FORMAT_SIMPLE
              LOAD_CONST               3 (', got ')
              LOAD_FAST_BORROW         5 (s)
              FORMAT_SIMPLE
              BUILD_STRING             6
              CALL                     1
              RAISE_VARARGS            1

130   L2:     LOAD_FAST_BORROW         5 (s)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C70CC60, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 133>:
133           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('points')

134           LOAD_CONST               2 ('List[Any]')

133           LOAD_CONST               3 ('return')

135           LOAD_CONST               4 ('List[Tuple[float, float]]')

133           BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object _design_points_to_tuples at 0x0000024B1C63EFB0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 133>:
 133           RESUME                   0

 137           LOAD_FAST_BORROW         0 (points)
               GET_ITER
               LOAD_FAST_AND_CLEAR      1 (pt)
               SWAP                     2
       L1:     BUILD_LIST               0
               SWAP                     2
       L2:     FOR_ITER                26 (to L3)
               STORE_FAST_LOAD_FAST    17 (pt, pt)
               LOAD_ATTR                0 (x)
               LOAD_FAST_BORROW         1 (pt)
               LOAD_ATTR                2 (y)
               BUILD_TUPLE              2
               LIST_APPEND              2
               JUMP_BACKWARD           28 (to L2)
       L3:     END_FOR
               POP_ITER
       L4:     SWAP                     2
               STORE_FAST               1 (pt)
               RETURN_VALUE

  --   L5:     SWAP                     2
               POP_TOP

 137           SWAP                     2
               STORE_FAST               1 (pt)
               RERAISE                  0
ExceptionTable:
  L1 to L4 -> L5 [2]

Disassembly of <code object __annotate__ at 0x0000024B1C70D2F0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 140>:
140           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('intent')
              LOAD_CONST               2 ('CamIntentV1')
              LOAD_CONST               3 ('return')
              LOAD_CONST               4 ('PocketIntentAdaptation')
              BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object pocket_params_from_intent at 0x0000024B1C4F8060, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\intent_adapter.py", line 140>:
 140           RESUME                   0

 171           BUILD_LIST               0
               STORE_FAST               1 (issues)

 174           LOAD_GLOBAL              1 (validate_pocket_design + NULL)
               LOAD_FAST_BORROW         0 (intent)
               LOAD_ATTR                2 (design)
               CALL                     1
               STORE_FAST               2 (design)

 177           LOAD_GLOBAL              5 (_design_points_to_tuples + NULL)
               LOAD_FAST_BORROW         2 (design)
               LOAD_ATTR                6 (boundary)
               CALL                     1
               STORE_FAST               3 (boundary)

 182           LOAD_FAST_BORROW         2 (design)
               LOAD_ATTR                8 (islands)
               GET_ITER

 180           LOAD_FAST_AND_CLEAR      4 (island)
               SWAP                     2
       L1:     BUILD_LIST               0
               SWAP                     2

 182   L2:     FOR_ITER                24 (to L3)
               STORE_FAST               4 (island)

 181           LOAD_GLOBAL              5 (_design_points_to_tuples + NULL)
               LOAD_FAST_BORROW         4 (island)
               LOAD_ATTR                6 (boundary)
               CALL                     1
               LIST_APPEND              2
               JUMP_BACKWARD           26 (to L2)

 182   L3:     END_FOR
               POP_ITER

 180   L4:     STORE_FAST               5 (islands)
               STORE_FAST               4 (island)

 186           LOAD_FAST_BORROW         3 (boundary)
               BUILD_LIST               1
               LOAD_FAST_BORROW         5 (islands)
               BINARY_OP                0 (+)
               STORE_FAST               6 (loops)

 189           LOAD_FAST_BORROW         0 (intent)
               LOAD_ATTR               10 (context)
               COPY                     1
               TO_BOOL
               POP_JUMP_IF_TRUE         3 (to L5)
               NOT_TAKEN
               POP_TOP
               BUILD_MAP                0
       L5:     STORE_FAST               7 (context)

 193           LOAD_FAST_BORROW         2 (design)
               LOAD_ATTR               12 (stepover_percent)
               LOAD_CONST               1 (100.0)
               BINARY_OP               11 (/)
               STORE_FAST               8 (stepover_fraction)

 196           LOAD_GLOBAL             15 (_extract_context_float + NULL)

 197           LOAD_FAST_BORROW         7 (context)
               LOAD_CONST               2 ('stepdown_mm')
               LOAD_CONST               3 (3.0)
               LOAD_CONST               4 (0.1)
               LOAD_CONST               5 (25.0)

 196           LOAD_CONST               6 (('default', 'ge', 'le'))
               CALL_KW                  5
               STORE_FAST               9 (stepdown)

 199           LOAD_GLOBAL             15 (_extract_context_float + NULL)

 200           LOAD_FAST_BORROW         7 (context)
               LOAD_CONST               7 ('margin_mm')
               LOAD_CONST               8 (0.0)
               LOAD_CONST               8 (0.0)
               LOAD_CONST               9 (10.0)

 199           LOAD_CONST               6 (('default', 'ge', 'le'))
               CALL_KW                  5
               STORE_FAST              10 (margin)

 202           LOAD_GLOBAL             17 (_extract_context_str + NULL)

 203           LOAD_FAST_BORROW         7 (context)
               LOAD_CONST              10 ('strategy')
               LOAD_CONST              11 ('Spiral')
               LOAD_CONST              11 ('Spiral')
               LOAD_CONST              12 ('Lanes')
               BUILD_LIST               2

 202           LOAD_CONST              13 (('default', 'allowed'))
               CALL_KW                  4
               STORE_FAST              11 (strategy)

 205           LOAD_GLOBAL             15 (_extract_context_float + NULL)

 206           LOAD_FAST_BORROW         7 (context)
               LOAD_CONST              14 ('smoothing_radius_mm')
               LOAD_CONST              15 (0.5)
               LOAD_CONST               8 (0.0)
               LOAD_CONST               9 (10.0)

 205           LOAD_CONST               6 (('default', 'ge', 'le'))
               CALL_KW                  5
               STORE_FAST              12 (smoothing_radius)

 210           LOAD_GLOBAL             15 (_extract_context_float + NULL)

 211           LOAD_FAST_BORROW         7 (context)
               LOAD_CONST              16 ('feed_rate_mm_min')
               LOAD_CONST              17 (1500.0)
               LOAD_CONST              18 (50.0)
               LOAD_CONST              19 (10000.0)

 210           LOAD_CONST               6 (('default', 'ge', 'le'))
               CALL_KW                  5
               STORE_FAST              13 (feed_xy)

 213           LOAD_GLOBAL             15 (_extract_context_float + NULL)

 214           LOAD_FAST_BORROW         7 (context)
               LOAD_CONST              20 ('plunge_rate_mm_min')
               LOAD_CONST              21 (500.0)
               LOAD_CONST              18 (50.0)
               LOAD_CONST              22 (2000.0)

 213           LOAD_CONST               6 (('default', 'ge', 'le'))
               CALL_KW                  5
               STORE_FAST              14 (plunge_rate)

 216           LOAD_GLOBAL             15 (_extract_context_float + NULL)

 217           LOAD_FAST_BORROW         7 (context)
               LOAD_CONST              23 ('safe_z_mm')
               LOAD_CONST               9 (10.0)
               LOAD_CONST              24 (1.0)
               LOAD_CONST               1 (100.0)

 216           LOAD_CONST               6 (('default', 'ge', 'le'))
               CALL_KW                  5
               STORE_FAST              15 (safe_z)

 219           LOAD_GLOBAL             15 (_extract_context_float + NULL)

 220           LOAD_FAST_BORROW         7 (context)
               LOAD_CONST              25 ('retract_z_mm')
               LOAD_CONST              26 (5.0)
               LOAD_CONST              15 (0.5)
               LOAD_CONST              18 (50.0)

 219           LOAD_CONST               6 (('default', 'ge', 'le'))
               CALL_KW                  5
               STORE_FAST              16 (retract_z)

 223           LOAD_GLOBAL             19 (PocketIntentAdaptation + NULL)

 224           LOAD_FAST_BORROW         6 (loops)

 225           LOAD_FAST_BORROW         2 (design)
               LOAD_ATTR               20 (tool_diameter_mm)

 226           LOAD_FAST_BORROW         8 (stepover_fraction)

 227           LOAD_FAST_BORROW         9 (stepdown)

 228           LOAD_FAST_BORROW        10 (margin)

 229           LOAD_FAST_BORROW        11 (strategy)

 230           LOAD_FAST_BORROW        12 (smoothing_radius)

 231           LOAD_FAST_BORROW        13 (feed_xy)

 232           LOAD_FAST_BORROW        14 (plunge_rate)

 233           LOAD_FAST_BORROW        15 (safe_z)

 234           LOAD_FAST_BORROW        16 (retract_z)

 235           LOAD_FAST_BORROW         2 (design)
               LOAD_ATTR               22 (pocket_depth_mm)

 236           LOAD_FAST_BORROW         2 (design)
               LOAD_ATTR               24 (finish_pass)

 237           LOAD_FAST_BORROW         2 (design)
               LOAD_ATTR               26 (finish_allowance_mm)

 238           LOAD_FAST_BORROW         1 (issues)

 223           LOAD_CONST              27 (('loops', 'tool_d', 'stepover', 'stepdown', 'margin', 'strategy', 'smoothing_radius', 'feed_xy', 'plunge_rate', 'safe_z', 'retract_z', 'pocket_depth_mm', 'finish_pass', 'finish_allowance_mm', 'issues'))
               CALL_KW                 15
               RETURN_VALUE

  --   L6:     SWAP                     2
               POP_TOP

 180           SWAP                     2
               STORE_FAST               4 (island)
               RERAISE                  0
ExceptionTable:
  L1 to L4 -> L6 [2]

```
---

## `cam/pocketing/__init__`  
`app/cam/pocketing/__pycache__/__init__.cpython-314.pyc` — 1940 bytes, mtime(UTC) 2026-05-25T19:12:27.115079

### Recovered structure (names + string constants)
```
<<module>> names=['__doc__', 'intent_schema', 'PocketDesignV1', 'PocketIslandV1', 'PocketPointV1', 'validate_pocket_design', 'intent_adapter', 'PocketIntentAdaptation', 'pocket_params_from_intent', '__getattr__', '__all__']
  <__getattr__> names=['', 'feasibility', 'getattr', 'AttributeError', '__name__']
    str: 'Lazy import for feasibility module (requires shapely).'
    str: 'module '
    str: ' has no attribute '
```

### Full disassembly (`dis.dis`)
```
  0           RESUME                   0

  1           LOAD_CONST               0 ('\nCAM Pocketing Module\n\nArea-clearing pocketing operations using the L.1 adaptive core.\n\nOperations:\n- Area clearing with zigzag/spiral patterns\n- Island (no-cut region) handling\n- Roughing and finishing passes\n\nUsage:\n    from app.cam.pocketing import (\n        PocketDesignV1,\n        validate_pocket_design,\n        pocket_params_from_intent,\n        compute_pocket_feasibility,\n        PocketFeasibilityResult,\n    )\n\n    # From CamIntentV1\n    adaptation = pocket_params_from_intent(intent)\n\n    # Check feasibility\n    feasibility = compute_pocket_feasibility(\n        boundary=adaptation.loops[0],\n        islands=adaptation.loops[1:],\n        ...\n    )\n\n    # Generate toolpath via L.1\n    from app.cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath\n    path_pts = plan_adaptive_l1(\n        loops=adaptation.loops,\n        tool_d=adaptation.tool_d,\n        stepover=adaptation.stepover,\n        ...\n    )\n')
              STORE_NAME               0 (__doc__)

 41           LOAD_SMALL_INT           1
              LOAD_CONST               1 (('PocketDesignV1', 'PocketIslandV1', 'PocketPointV1', 'validate_pocket_design'))
              IMPORT_NAME              1 (intent_schema)
              IMPORT_FROM              2 (PocketDesignV1)
              STORE_NAME               2 (PocketDesignV1)
              IMPORT_FROM              3 (PocketIslandV1)
              STORE_NAME               3 (PocketIslandV1)
              IMPORT_FROM              4 (PocketPointV1)
              STORE_NAME               4 (PocketPointV1)
              IMPORT_FROM              5 (validate_pocket_design)
              STORE_NAME               5 (validate_pocket_design)
              POP_TOP

 49           LOAD_SMALL_INT           1
              LOAD_CONST               2 (('PocketIntentAdaptation', 'pocket_params_from_intent'))
              IMPORT_NAME              6 (intent_adapter)
              IMPORT_FROM              7 (PocketIntentAdaptation)
              STORE_NAME               7 (PocketIntentAdaptation)
              IMPORT_FROM              8 (pocket_params_from_intent)
              STORE_NAME               8 (pocket_params_from_intent)
              POP_TOP

 55           LOAD_CONST               3 (<code object __getattr__ at 0x0000024B1C63F210, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\__init__.py", line 55>)
              MAKE_FUNCTION
              STORE_NAME               9 (__getattr__)

 68           BUILD_LIST               0
              LOAD_CONST               5 (('PocketDesignV1', 'PocketIslandV1', 'PocketPointV1', 'validate_pocket_design', 'PocketIntentAdaptation', 'pocket_params_from_intent', 'PocketFeasibilityResult', 'compute_pocket_feasibility', 'compute_pocket_area', 'hash_feasibility_result'))
              LIST_EXTEND              1
              STORE_NAME              10 (__all__)
              LOAD_CONST               4 (None)
              RETURN_VALUE

Disassembly of <code object __getattr__ at 0x0000024B1C63F210, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\pocketing\__init__.py", line 55>:
 55           RESUME                   0

 57           LOAD_FAST_BORROW         0 (name)
              LOAD_CONST               4 (('PocketFeasibilityResult', 'compute_pocket_feasibility', 'compute_pocket_area', 'hash_feasibility_result'))
              CONTAINS_OP              0 (in)
              POP_JUMP_IF_FALSE       18 (to L1)
              NOT_TAKEN

 63           LOAD_SMALL_INT           1
              LOAD_CONST               1 (('feasibility',))
              IMPORT_NAME              0
              IMPORT_FROM              1 (feasibility)
              STORE_FAST               1 (feasibility)
              POP_TOP

 64           LOAD_GLOBAL              5 (getattr + NULL)
              LOAD_FAST_BORROW_LOAD_FAST_BORROW 16 (feasibility, name)
              CALL                     2
              RETURN_VALUE

 65   L1:     LOAD_GLOBAL              7 (AttributeError + NULL)
              LOAD_CONST               2 ('module ')
              LOAD_GLOBAL              8 (__name__)
              CONVERT_VALUE            2 (repr)
              FORMAT_SIMPLE
              LOAD_CONST               3 (' has no attribute ')
              LOAD_FAST_BORROW         0 (name)
              CONVERT_VALUE            2 (repr)
              FORMAT_SIMPLE
              BUILD_STRING             4
              CALL                     1
              RAISE_VARARGS            1

```
---

## `cam/routers/pocketing/intent_router`  
`app/cam/routers/pocketing/__pycache__/intent_router.cpython-314.pyc` — 18009 bytes, mtime(UTC) 2026-05-25T19:48:06.060819

### Recovered structure (names + string constants)
```
<<module>> names=['__doc__', '__future__', 'annotations', 'logging', 'math', 'datetime', 'timezone', 'typing', 'Any', 'Dict', 'List', 'fastapi', 'APIRouter', 'HTTPException', 'pydantic', 'BaseModel', 'Field', 'app.rmos.cam.schemas_intent', 'CamIntentV1', 'CamModeV1', 'app.rmos.cam.normalize_intent', 'normalize_cam_intent_v1', 'CamIntentIssue', 'CamIntentValidationError', 'app.cam.pocketing', 'validate_pocket_design', 'pocket_params_from_intent', 'HAS_FEASIBILITY', 'compute_pocket_feasibility', 'hash_feasibility_result']
  str: 'PocketingIntentIssue'
  str: 'PocketingIntentMetadata'
  str: 'PocketingIntentResponse'
  str: '/intent-gcode'
  <PocketingIntentIssue> names=['__name__', '__module__', '__qualname__', '__firstlineno__', '__doc__', '__annotations__', 'path', '__static_attributes__']
    str: 'PocketingIntentIssue'
    str: 'Normalization issue from CamIntentV1 processing.'
    str: 'str'
    str: 'code'
    str: 'message'
    str: 'path'
  <PocketingIntentMetadata> names=['__name__', '__module__', '__qualname__', '__firstlineno__', '__doc__', 'Field', 'pocket_area_mm2', '__annotations__', 'island_count', 'stepover_percent', 'estimated_time_seconds', '__static_attributes__']
    str: 'PocketingIntentMetadata'
    str: 'Metadata from pocketing generation.'
    str: 'Pocket area in mm²'
    str: 'float'
    str: 'pocket_area_mm2'
    str: 'Number of islands'
    str: 'int'
    str: 'island_count'
    str: 'Stepover percentage'
    str: 'stepover_percent'
    str: 'Estimated machining time'
    str: 'estimated_time_seconds'
  <PocketingIntentResponse> names=['__name__', '__module__', '__qualname__', '__firstlineno__', '__doc__', 'Field', 'gcode', '__annotations__', 'list', 'issues', 'run_id', 'dict', 'hashes', 'metadata', '__static_attributes__']
    str: 'PocketingIntentResponse'
    str: 'Response from Pocketing intent endpoint.'
    str: 'Generated G-code'
    str: 'str'
    str: 'gcode'
    str: 'Normalization issues (soft warnings)'
    str: 'List[PocketingIntentIssue]'
    str: 'issues'
    str: 'RMOS run artifact ID'
    str: 'run_id'
    str: 'SHA256 hashes for provenance'
    str: 'Dict[str, str]'
    str: 'hashes'
    str: 'Pocketing generation metadata'
    str: 'PocketingIntentMetadata'
    str: 'metadata'
  <__annotate__> names=[]
    str: 'issues'
    str: 'List[CamIntentIssue]'
    str: 'return'
    str: 'List[PocketingIntentIssue]'
  <_issues_to_response> names=['PocketingIntentIssue', 'code', 'message', 'path']
    str: 'Convert internal issues to response format.'
  <__annotate__> names=[]
    str: 'moves'
    str: 'List[Dict[str, Any]]'
    str: 'spindle_rpm'
    str: 'int'
    str: 'return'
    str: 'str'
  <_moves_to_gcode> names=['get', 'append', 'join', 'extend']
    str: 'Convert L.1 move list to G-code string.'
    str: '(Pocketing Operation - L.1 Adaptive Core)'
    str: 'G90 (Absolute positioning)'
    str: 'G21 (Units: mm)'
    str: 'M3 S'
    str: ' (Spindle on)'
    str: 'G4 P2 (Dwell for spindle)'
    str: 'code'
    str: 'G1'
    str: 'x'
    str: 'X'
    str: '.3f'
    str: 'y'
    str: 'Y'
    str: 'z'
    str: 'Z'
    str: 'f'
    str: 'F'
    str: '.0f'
  <__annotate__> names=[]
    str: 'path_pts'
    str: 'List'
    str: 'feed_xy'
    str: 'float'
    str: 'pocket_depth'
    str: 'stepdown'
    str: 'plunge_rate'
    str: 'return'
  <_estimate_time> names=['range', 'len', 'math', 'hypot', 'max', 'int', 'ceil']
    str: 'Estimate machining time in seconds.'
  <__annotate__> names=[]
    str: 'intent'
    str: 'CamIntentV1'
    str: 'return'
    str: 'PocketingIntentResponse'
  <generate_pocketing_intent_gcode> names=['HAS_FEASIBILITY', 'HTTPException', 'HAS_L1_CORE', 'datetime', 'now', 'timezone', 'utc', 'isoformat', 'sha256_of_obj', 'model_dump', 'tool_id', 'normalize_cam_intent_v1', 'CamIntentValidationError', 'str', 'issues', 'code', 'message', 'path', 'mode', 'CamModeV1', 'ROUTER_3AXIS', 'value', 'validate_pocket_design', 'design', 'ValueError', 'pocket_params_from_intent', 'loops', 'len', 'compute_pocket_feasibility', 'pocket_depth_mm']
    str: 'error'
    str: 'DEPENDENCY_UNAVAILABLE'
    str: 'message'
    str: 'Pocketing feasibility requires shapely which is not available (Python 3.14 numpy issue)'
    str: 'Pocketing requires L.1 adaptive core which is not available'
    str: 'pocketing:intent'
    str: 'NORMALIZATION_ERROR'
    str: 'issues'
    str: 'code'
    str: 'path'
    str: 'INVALID_MODE'
    str: 'Pocketing requires mode=router_3axis, got '
    str: 'expected'
    str: 'router_3axis'
    str: 'actual'
    str: 'INVALID_DESIGN'
    str: 'ADAPTER_ERROR'
    str: 'pocketing_intent'
    str: 'pocketing_intent_gcode_blocked'
    str: 'BLOCKED'
    str: 'Blocked by feasibility check: '
    str: ', '
    str: 'Feasibility issues: '
    str: 'FEASIBILITY_BLOCKED'
    str: 'Pocketing G-code generation blocked by feasibility check.'
    str: 'run_id'
    str: 'feasibility'
    str: 'L.1 returned empty toolpath'
    str: 'L.1 toolpath generation failed: %s'
    str: 'pocketing_intent_gcode_execution'
    str: 'ERROR'
    str: ': '
    str: 'TOOLPATH_GENERATION_ERROR'
    str: 'L.1 toolpath generation failed: '
    str: '(Pocketing Operation - L.1 Adaptive Core)'
    str: '(Pocket depth: '
    str: 'mm in '
    str: ' passes)'
    str: '(Tool: '
    str: 'mm, Stepover: '
    str: '.0f'
    str: '%)'
    str: '(Islands: '
    str: ')'
    str: 'G90 (Absolute positioning)'
    str: 'G21 (Units: mm)'
    str: 'M3 S18000 (Spindle on)'
    str: 'G4 P2 (Dwell for spindle)'
    str: 'G0 Z'
    str: '.3f'
    str: ' (Safe height)'
    str: '(--- Pass '
    str: ': Z = '
    str: ' ---)'
    str: 'G1'
    str: 'x'
    str: 'X'
    str: 'y'
    str: 'Y'
    str: 'z'
    str: 'Z'
    str: 'f'
    str: 'F'
    str: 'M5 (Spindle off)'
    str: 'M30 (Program end)'
    str: 'Generated G-code is empty'
    str: 'G-code generation failed: %s'
    str: 'GCODE_GENERATION_ERROR'
    str: 'G-code generation failed: '
    str: 'OK'
    str: 'request_sha256'
    str: 'feasibility_sha256'
    str: 'gcode_sha256'
    str: 'pocket_area_mm2'
```

### Full disassembly (`dis.dis`)
```
   0            RESUME                   0

   1            LOAD_CONST               0 ('\nPocketing Intent Router\n\nCamIntentV1-based endpoint for Pocketing operations.\nPart of the CAM Intent First-Endpoint Migration (ADR-003).\n\nThis is the canonical path for Pocketing operations through the unified\nCamIntentV1 contract. The legacy endpoints remain live under\nFeature Parity Migration Policy until this path is proven.\n\nEndpoint: POST /api/cam/pocketing/intent-gcode\n\nLANE: OPERATION - Uses normalize_cam_intent_v1, runs feasibility,\npersists RMOS artifact, writes audit trail.\n')
                STORE_NAME               0 (__doc__)

  16            LOAD_SMALL_INT           0
                LOAD_CONST               1 (('annotations',))
                IMPORT_NAME              1 (__future__)
                IMPORT_FROM              2 (annotations)
                STORE_NAME               2 (annotations)
                POP_TOP

  18            LOAD_SMALL_INT           0
                LOAD_CONST               2 (None)
                IMPORT_NAME              3 (logging)
                STORE_NAME               3 (logging)

  19            LOAD_SMALL_INT           0
                LOAD_CONST               2 (None)
                IMPORT_NAME              4 (math)
                STORE_NAME               4 (math)

  20            LOAD_SMALL_INT           0
                LOAD_CONST               3 (('datetime', 'timezone'))
                IMPORT_NAME              5 (datetime)
                IMPORT_FROM              5 (datetime)
                STORE_NAME               5 (datetime)
                IMPORT_FROM              6 (timezone)
                STORE_NAME               6 (timezone)
                POP_TOP

  21            LOAD_SMALL_INT           0
                LOAD_CONST               4 (('Any', 'Dict', 'List'))
                IMPORT_NAME              7 (typing)
                IMPORT_FROM              8 (Any)
                STORE_NAME               8 (Any)
                IMPORT_FROM              9 (Dict)
                STORE_NAME               9 (Dict)
                IMPORT_FROM             10 (List)
                STORE_NAME              10 (List)
                POP_TOP

  23            LOAD_SMALL_INT           0
                LOAD_CONST               5 (('APIRouter', 'HTTPException'))
                IMPORT_NAME             11 (fastapi)
                IMPORT_FROM             12 (APIRouter)
                STORE_NAME              12 (APIRouter)
                IMPORT_FROM             13 (HTTPException)
                STORE_NAME              13 (HTTPException)
                POP_TOP

  24            LOAD_SMALL_INT           0
                LOAD_CONST               6 (('BaseModel', 'Field'))
                IMPORT_NAME             14 (pydantic)
                IMPORT_FROM             15 (BaseModel)
                STORE_NAME              15 (BaseModel)
                IMPORT_FROM             16 (Field)
                STORE_NAME              16 (Field)
                POP_TOP

  26            LOAD_SMALL_INT           0
                LOAD_CONST               7 (('CamIntentV1', 'CamModeV1'))
                IMPORT_NAME             17 (app.rmos.cam.schemas_intent)
                IMPORT_FROM             18 (CamIntentV1)
                STORE_NAME              18 (CamIntentV1)
                IMPORT_FROM             19 (CamModeV1)
                STORE_NAME              19 (CamModeV1)
                POP_TOP

  27            LOAD_SMALL_INT           0
                LOAD_CONST               8 (('normalize_cam_intent_v1', 'CamIntentIssue', 'CamIntentValidationError'))
                IMPORT_NAME             20 (app.rmos.cam.normalize_intent)
                IMPORT_FROM             21 (normalize_cam_intent_v1)
                STORE_NAME              21 (normalize_cam_intent_v1)
                IMPORT_FROM             22 (CamIntentIssue)
                STORE_NAME              22 (CamIntentIssue)
                IMPORT_FROM             23 (CamIntentValidationError)
                STORE_NAME              23 (CamIntentValidationError)
                POP_TOP

  32            LOAD_SMALL_INT           0
                LOAD_CONST               9 (('validate_pocket_design', 'pocket_params_from_intent'))
                IMPORT_NAME             24 (app.cam.pocketing)
                IMPORT_FROM             25 (validate_pocket_design)
                STORE_NAME              25 (validate_pocket_design)
                IMPORT_FROM             26 (pocket_params_from_intent)
                STORE_NAME              26 (pocket_params_from_intent)
                POP_TOP

  38            LOAD_CONST              10 (True)
                STORE_NAME              27 (HAS_FEASIBILITY)

  39            NOP

  40    L1:     LOAD_SMALL_INT           0
                LOAD_CONST              11 (('compute_pocket_feasibility', 'hash_feasibility_result'))
                IMPORT_NAME             24 (app.cam.pocketing)
                IMPORT_FROM             28 (compute_pocket_feasibility)
                STORE_NAME              28 (compute_pocket_feasibility)
                IMPORT_FROM             29 (hash_feasibility_result)
                STORE_NAME              29 (hash_feasibility_result)
                POP_TOP

  49    L2:     NOP

  50    L3:     LOAD_SMALL_INT           0
                LOAD_CONST              13 (('plan_adaptive_l1', 'to_toolpath'))
                IMPORT_NAME             31 (app.cam.adaptive_core_l1)
                IMPORT_FROM             32 (plan_adaptive_l1)
                STORE_NAME              32 (plan_adaptive_l1)
                IMPORT_FROM             33 (to_toolpath)
                STORE_NAME              33 (to_toolpath)
                POP_TOP

  51            LOAD_CONST              10 (True)
                STORE_NAME              34 (HAS_L1_CORE)

  56    L4:     LOAD_SMALL_INT           0
                LOAD_CONST              14 (('RunArtifact', 'RunDecision', 'Hashes', 'persist_run', 'create_run_id', 'sha256_of_obj', 'sha256_of_text'))
                IMPORT_NAME             35 (app.rmos.runs_v2)
                IMPORT_FROM             36 (RunArtifact)
                STORE_NAME              36 (RunArtifact)
                IMPORT_FROM             37 (RunDecision)
                STORE_NAME              37 (RunDecision)
                IMPORT_FROM             38 (Hashes)
                STORE_NAME              38 (Hashes)
                IMPORT_FROM             39 (persist_run)
                STORE_NAME              39 (persist_run)
                IMPORT_FROM             40 (create_run_id)
                STORE_NAME              40 (create_run_id)
                IMPORT_FROM             41 (sha256_of_obj)
                STORE_NAME              41 (sha256_of_obj)
                IMPORT_FROM             42 (sha256_of_text)
                STORE_NAME              42 (sha256_of_text)
                POP_TOP

  66            LOAD_NAME                3 (logging)
                LOAD_ATTR               86 (getLogger)
                PUSH_NULL
                LOAD_NAME               44 (__name__)
                CALL                     1
                STORE_NAME              45 (logger)

  68            LOAD_NAME               12 (APIRouter)
                PUSH_NULL
                CALL                     0
                STORE_NAME              46 (router)

  71            LOAD_BUILD_CLASS
                PUSH_NULL
                LOAD_CONST              15 (<code object PocketingIntentIssue at 0x0000024B1C696DE0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 71>)
                MAKE_FUNCTION
                LOAD_CONST              16 ('PocketingIntentIssue')
                LOAD_NAME               15 (BaseModel)
                CALL                     3
                STORE_NAME              47 (PocketingIntentIssue)

  79            LOAD_BUILD_CLASS
                PUSH_NULL
                LOAD_CONST              17 (<code object PocketingIntentMetadata at 0x0000024B1C5D39B0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 79>)
                MAKE_FUNCTION
                LOAD_CONST              18 ('PocketingIntentMetadata')
                LOAD_NAME               15 (BaseModel)
                CALL                     3
                STORE_NAME              48 (PocketingIntentMetadata)

  88            LOAD_BUILD_CLASS
                PUSH_NULL
                LOAD_CONST              19 (<code object PocketingIntentResponse at 0x0000024B1C6DDAC0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 88>)
                MAKE_FUNCTION
                LOAD_CONST              20 ('PocketingIntentResponse')
                LOAD_NAME               15 (BaseModel)
                CALL                     3
                STORE_NAME              49 (PocketingIntentResponse)

 107            LOAD_CONST              21 (<code object __annotate__ at 0x0000024B1C5EBE10, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 107>)
                MAKE_FUNCTION
                LOAD_CONST              22 (<code object _issues_to_response at 0x0000024B1C62DA50, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 107>)
                MAKE_FUNCTION
                SET_FUNCTION_ATTRIBUTE  16 (annotate)
                STORE_NAME              50 (_issues_to_response)

 115            LOAD_CONST              31 ((18000,))
                LOAD_CONST              23 (<code object __annotate__ at 0x0000024B1C6D2230, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 115>)
                MAKE_FUNCTION
                LOAD_CONST              24 (<code object _moves_to_gcode at 0x0000024B1C408660, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 115>)
                MAKE_FUNCTION
                SET_FUNCTION_ATTRIBUTE  16 (annotate)
                SET_FUNCTION_ATTRIBUTE   1 (defaults)
                STORE_NAME              51 (_moves_to_gcode)

 150            LOAD_CONST              25 (<code object __annotate__ at 0x0000024B1C6D2330, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 150>)
                MAKE_FUNCTION
                LOAD_CONST              26 (<code object _estimate_time at 0x0000024B1C4F5E10, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 150>)
                MAKE_FUNCTION
                SET_FUNCTION_ATTRIBUTE  16 (annotate)
                STORE_NAME              52 (_estimate_time)

 183            LOAD_NAME               46 (router)
                LOAD_ATTR              107 (post + NULL|self)
                LOAD_CONST              27 ('/intent-gcode')
                LOAD_NAME               49 (PocketingIntentResponse)
                LOAD_CONST              28 (('response_model',))
                CALL_KW                  2

 184            LOAD_CONST              29 (<code object __annotate__ at 0x0000024B1C70CC60, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 184>)
                MAKE_FUNCTION
                LOAD_CONST              30 (<code object generate_pocketing_intent_gcode at 0x0000024B1C5362D0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 183>)
                MAKE_FUNCTION
                SET_FUNCTION_ATTRIBUTE  16 (annotate)

 183            CALL                     0

 184            STORE_NAME              54 (generate_pocketing_intent_gcode)
                LOAD_CONST               2 (None)
                RETURN_VALUE

  --    L5:     PUSH_EXC_INFO

  44            LOAD_NAME               30 (ImportError)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE       10 (to L7)
                NOT_TAKEN
                POP_TOP

  45            LOAD_CONST              12 (False)
                STORE_NAME              27 (HAS_FEASIBILITY)

  46            LOAD_CONST               2 (None)
                STORE_NAME              28 (compute_pocket_feasibility)

  47            LOAD_CONST               2 (None)
                STORE_NAME              29 (hash_feasibility_result)
        L6:     POP_EXCEPT
                JUMP_BACKWARD_NO_INTERRUPT 152 (to L2)

  44    L7:     RERAISE                  0

  --    L8:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
        L9:     PUSH_EXC_INFO

  52            LOAD_NAME               30 (ImportError)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE       10 (to L11)
                NOT_TAKEN
                POP_TOP

  53            LOAD_CONST              12 (False)
                STORE_NAME              34 (HAS_L1_CORE)

  54            LOAD_CONST               2 (None)
                STORE_NAME              32 (plan_adaptive_l1)

  55            LOAD_CONST               2 (None)
                STORE_NAME              33 (to_toolpath)
       L10:     POP_EXCEPT
                JUMP_BACKWARD_NO_INTERRUPT 160 (to L4)

  52   L11:     RERAISE                  0

  --   L12:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
ExceptionTable:
  L1 to L2 -> L5 [0]
  L3 to L4 -> L9 [0]
  L5 to L6 -> L8 [1] lasti
  L7 to L8 -> L8 [1] lasti
  L9 to L10 -> L12 [1] lasti
  L11 to L12 -> L12 [1] lasti

Disassembly of <code object PocketingIntentIssue at 0x0000024B1C696DE0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 71>:
 71           RESUME                   0
              LOAD_NAME                0 (__name__)
              STORE_NAME               1 (__module__)
              LOAD_CONST               0 ('PocketingIntentIssue')
              STORE_NAME               2 (__qualname__)
              LOAD_SMALL_INT          71
              STORE_NAME               3 (__firstlineno__)
              SETUP_ANNOTATIONS

 72           LOAD_CONST               1 ('Normalization issue from CamIntentV1 processing.')
              STORE_NAME               4 (__doc__)

 74           LOAD_CONST               2 ('str')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               3 ('code')
              STORE_SUBSCR

 75           LOAD_CONST               2 ('str')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               4 ('message')
              STORE_SUBSCR

 76           LOAD_CONST               5 ('')
              STORE_NAME               6 (path)
              LOAD_CONST               2 ('str')
              LOAD_NAME                5 (__annotations__)
              LOAD_CONST               6 ('path')
              STORE_SUBSCR
              LOAD_CONST               7 (())
              STORE_NAME               7 (__static_attributes__)
              LOAD_CONST               8 (None)
              RETURN_VALUE

Disassembly of <code object PocketingIntentMetadata at 0x0000024B1C5D39B0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 79>:
 79           RESUME                   0
              LOAD_NAME                0 (__name__)
              STORE_NAME               1 (__module__)
              LOAD_CONST               0 ('PocketingIntentMetadata')
              STORE_NAME               2 (__qualname__)
              LOAD_SMALL_INT          79
              STORE_NAME               3 (__firstlineno__)
              SETUP_ANNOTATIONS

 80           LOAD_CONST               1 ('Metadata from pocketing generation.')
              STORE_NAME               4 (__doc__)

 82           LOAD_NAME                5 (Field)
              PUSH_NULL
              LOAD_CONST               2 (Ellipsis)
              LOAD_CONST               3 ('Pocket area in mm²')
              LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME               6 (pocket_area_mm2)
              LOAD_CONST               5 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST               6 ('pocket_area_mm2')
              STORE_SUBSCR

 83           LOAD_NAME                5 (Field)
              PUSH_NULL
              LOAD_CONST               2 (Ellipsis)
              LOAD_CONST               7 ('Number of islands')
              LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME               8 (island_count)
              LOAD_CONST               8 ('int')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST               9 ('island_count')
              STORE_SUBSCR

 84           LOAD_NAME                5 (Field)
              PUSH_NULL
              LOAD_CONST               2 (Ellipsis)
              LOAD_CONST              10 ('Stepover percentage')
              LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME               9 (stepover_percent)
              LOAD_CONST               5 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              11 ('stepover_percent')
              STORE_SUBSCR

 85           LOAD_NAME                5 (Field)
              PUSH_NULL
              LOAD_CONST               2 (Ellipsis)
              LOAD_CONST              12 ('Estimated machining time')
              LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME              10 (estimated_time_seconds)
              LOAD_CONST               5 ('float')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              13 ('estimated_time_seconds')
              STORE_SUBSCR
              LOAD_CONST              14 (())
              STORE_NAME              11 (__static_attributes__)
              LOAD_CONST              15 (None)
              RETURN_VALUE

Disassembly of <code object PocketingIntentResponse at 0x0000024B1C6DDAC0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 88>:
 88           RESUME                   0
              LOAD_NAME                0 (__name__)
              STORE_NAME               1 (__module__)
              LOAD_CONST               0 ('PocketingIntentResponse')
              STORE_NAME               2 (__qualname__)
              LOAD_SMALL_INT          88
              STORE_NAME               3 (__firstlineno__)
              SETUP_ANNOTATIONS

 89           LOAD_CONST               1 ('Response from Pocketing intent endpoint.')
              STORE_NAME               4 (__doc__)

 91           LOAD_NAME                5 (Field)
              PUSH_NULL
              LOAD_CONST               2 (Ellipsis)
              LOAD_CONST               3 ('Generated G-code')
              LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME               6 (gcode)
              LOAD_CONST               5 ('str')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST               6 ('gcode')
              STORE_SUBSCR

 92           LOAD_NAME                5 (Field)
              PUSH_NULL

 93           LOAD_NAME                8 (list)

 94           LOAD_CONST               7 ('Normalization issues (soft warnings)')

 92           LOAD_CONST               8 (('default_factory', 'description'))
              CALL_KW                  2
              STORE_NAME               9 (issues)
              LOAD_CONST               9 ('List[PocketingIntentIssue]')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              10 ('issues')
              STORE_SUBSCR

 96           LOAD_NAME                5 (Field)
              PUSH_NULL
              LOAD_CONST               2 (Ellipsis)
              LOAD_CONST              11 ('RMOS run artifact ID')
              LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME              10 (run_id)
              LOAD_CONST               5 ('str')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              12 ('run_id')
              STORE_SUBSCR

 97           LOAD_NAME                5 (Field)
              PUSH_NULL

 98           LOAD_NAME               11 (dict)

 99           LOAD_CONST              13 ('SHA256 hashes for provenance')

 97           LOAD_CONST               8 (('default_factory', 'description'))
              CALL_KW                  2
              STORE_NAME              12 (hashes)
              LOAD_CONST              14 ('Dict[str, str]')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              15 ('hashes')
              STORE_SUBSCR

101           LOAD_NAME                5 (Field)
              PUSH_NULL

102           LOAD_CONST               2 (Ellipsis)

103           LOAD_CONST              16 ('Pocketing generation metadata')

101           LOAD_CONST               4 (('description',))
              CALL_KW                  2
              STORE_NAME              13 (metadata)
              LOAD_CONST              17 ('PocketingIntentMetadata')
              LOAD_NAME                7 (__annotations__)
              LOAD_CONST              18 ('metadata')
              STORE_SUBSCR
              LOAD_CONST              19 (())
              STORE_NAME              14 (__static_attributes__)
              LOAD_CONST              20 (None)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C5EBE10, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 107>:
107           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('issues')
              LOAD_CONST               2 ('List[CamIntentIssue]')
              LOAD_CONST               3 ('return')
              LOAD_CONST               4 ('List[PocketingIntentIssue]')
              BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object _issues_to_response at 0x0000024B1C62DA50, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 107>:
 107           RESUME                   0

 111           LOAD_FAST_BORROW         0 (issues)
               GET_ITER

 109           LOAD_FAST_AND_CLEAR      1 (i)
               SWAP                     2
       L1:     BUILD_LIST               0
               SWAP                     2

 111   L2:     FOR_ITER                47 (to L3)
               STORE_FAST               1 (i)

 110           LOAD_GLOBAL              1 (PocketingIntentIssue + NULL)
               LOAD_FAST_BORROW         1 (i)
               LOAD_ATTR                2 (code)
               LOAD_FAST_BORROW         1 (i)
               LOAD_ATTR                4 (message)
               LOAD_FAST_BORROW         1 (i)
               LOAD_ATTR                6 (path)
               LOAD_CONST               1 (('code', 'message', 'path'))
               CALL_KW                  3
               LIST_APPEND              2
               JUMP_BACKWARD           49 (to L2)

 111   L3:     END_FOR
               POP_ITER

 109   L4:     SWAP                     2
               STORE_FAST               1 (i)
               RETURN_VALUE

  --   L5:     SWAP                     2
               POP_TOP

 109           SWAP                     2
               STORE_FAST               1 (i)
               RERAISE                  0
ExceptionTable:
  L1 to L4 -> L5 [2]

Disassembly of <code object __annotate__ at 0x0000024B1C6D2230, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 115>:
115           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('moves')
              LOAD_CONST               2 ('List[Dict[str, Any]]')
              LOAD_CONST               3 ('spindle_rpm')
              LOAD_CONST               4 ('int')
              LOAD_CONST               5 ('return')
              LOAD_CONST               6 ('str')
              BUILD_MAP                3
              RETURN_VALUE

Disassembly of <code object _moves_to_gcode at 0x0000024B1C408660, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 115>:
115           RESUME                   0

118           LOAD_CONST               1 ('(Pocketing Operation - L.1 Adaptive Core)')

119           LOAD_CONST               2 ('G90 (Absolute positioning)')

120           LOAD_CONST               3 ('G21 (Units: mm)')

121           LOAD_CONST               4 ('M3 S')
              LOAD_FAST_BORROW         1 (spindle_rpm)
              FORMAT_SIMPLE
              LOAD_CONST               5 (' (Spindle on)')
              BUILD_STRING             3

122           LOAD_CONST               6 ('G4 P2 (Dwell for spindle)')

123           LOAD_CONST               7 ('')

117           BUILD_LIST               6
              STORE_FAST               2 (lines)

126           LOAD_FAST_BORROW         0 (moves)
              GET_ITER
      L1:     FOR_ITER               196 (to L6)
              STORE_FAST               3 (move)

127           LOAD_FAST_BORROW         3 (move)
              LOAD_ATTR                1 (get + NULL|self)
              LOAD_CONST               8 ('code')
              LOAD_CONST               9 ('G1')
              CALL                     2
              STORE_FAST               4 (code)

128           LOAD_FAST_BORROW         4 (code)
              BUILD_LIST               1
              STORE_FAST               5 (parts)

130           LOAD_CONST              10 ('x')
              LOAD_FAST_BORROW         3 (move)
              CONTAINS_OP              0 (in)
              POP_JUMP_IF_FALSE       29 (to L2)
              NOT_TAKEN

131           LOAD_FAST_BORROW         5 (parts)
              LOAD_ATTR                3 (append + NULL|self)
              LOAD_CONST              11 ('X')
              LOAD_FAST_BORROW         3 (move)
              LOAD_CONST              10 ('x')
              BINARY_OP               26 ([])
              LOAD_CONST              12 ('.3f')
              FORMAT_WITH_SPEC
              BUILD_STRING             2
              CALL                     1
              POP_TOP

132   L2:     LOAD_CONST              13 ('y')
              LOAD_FAST_BORROW         3 (move)
              CONTAINS_OP              0 (in)
              POP_JUMP_IF_FALSE       29 (to L3)
              NOT_TAKEN

133           LOAD_FAST_BORROW         5 (parts)
              LOAD_ATTR                3 (append + NULL|self)
              LOAD_CONST              14 ('Y')
              LOAD_FAST_BORROW         3 (move)
              LOAD_CONST              13 ('y')
              BINARY_OP               26 ([])
              LOAD_CONST              12 ('.3f')
              FORMAT_WITH_SPEC
              BUILD_STRING             2
              CALL                     1
              POP_TOP

134   L3:     LOAD_CONST              15 ('z')
              LOAD_FAST_BORROW         3 (move)
              CONTAINS_OP              0 (in)
              POP_JUMP_IF_FALSE       29 (to L4)
              NOT_TAKEN

135           LOAD_FAST_BORROW         5 (parts)
              LOAD_ATTR                3 (append + NULL|self)
              LOAD_CONST              16 ('Z')
              LOAD_FAST_BORROW         3 (move)
              LOAD_CONST              15 ('z')
              BINARY_OP               26 ([])
              LOAD_CONST              12 ('.3f')
              FORMAT_WITH_SPEC
              BUILD_STRING             2
              CALL                     1
              POP_TOP

136   L4:     LOAD_CONST              17 ('f')
              LOAD_FAST_BORROW         3 (move)
              CONTAINS_OP              0 (in)
              POP_JUMP_IF_FALSE       29 (to L5)
              NOT_TAKEN

137           LOAD_FAST_BORROW         5 (parts)
              LOAD_ATTR                3 (append + NULL|self)
              LOAD_CONST              18 ('F')
              LOAD_FAST_BORROW         3 (move)
              LOAD_CONST              17 ('f')
              BINARY_OP               26 ([])
              LOAD_CONST              19 ('.0f')
              FORMAT_WITH_SPEC
              BUILD_STRING             2
              CALL                     1
              POP_TOP

139   L5:     LOAD_FAST_BORROW         2 (lines)
              LOAD_ATTR                3 (append + NULL|self)
              LOAD_CONST              20 (' ')
              LOAD_ATTR                5 (join + NULL|self)
              LOAD_FAST_BORROW         5 (parts)
              CALL                     1
              CALL                     1
              POP_TOP
              JUMP_BACKWARD          198 (to L1)

126   L6:     END_FOR
              POP_ITER

141           LOAD_FAST_BORROW         2 (lines)
              LOAD_ATTR                7 (extend + NULL|self)
              BUILD_LIST               0
              LOAD_CONST              22 (('', 'M5 (Spindle off)', 'M30 (Program end)'))
              LIST_EXTEND              1
              CALL                     1
              POP_TOP

147           LOAD_CONST              21 ('\n')
              LOAD_ATTR                5 (join + NULL|self)
              LOAD_FAST_BORROW         2 (lines)
              CALL                     1
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C6D2330, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 150>:
150           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('path_pts')

151           LOAD_CONST               2 ('List')

150           LOAD_CONST               3 ('feed_xy')

152           LOAD_CONST               4 ('float')

150           LOAD_CONST               5 ('pocket_depth')

153           LOAD_CONST               4 ('float')

150           LOAD_CONST               6 ('stepdown')

154           LOAD_CONST               4 ('float')

150           LOAD_CONST               7 ('plunge_rate')

155           LOAD_CONST               4 ('float')

150           LOAD_CONST               8 ('return')

156           LOAD_CONST               4 ('float')

150           BUILD_MAP                6
              RETURN_VALUE

Disassembly of <code object _estimate_time at 0x0000024B1C4F5E10, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 150>:
150           RESUME                   0

158           LOAD_FAST_BORROW         0 (path_pts)
              TO_BOOL
              POP_JUMP_IF_TRUE         3 (to L1)
              NOT_TAKEN

159           LOAD_CONST               1 (0.0)
              RETURN_VALUE

162   L1:     LOAD_CONST               1 (0.0)
              STORE_FAST               5 (path_length)

163           LOAD_GLOBAL              1 (range + NULL)
              LOAD_SMALL_INT           1
              LOAD_GLOBAL              3 (len + NULL)
              LOAD_FAST_BORROW         0 (path_pts)
              CALL                     1
              CALL                     2
              GET_ITER
      L2:     FOR_ITER               116 (to L3)
              STORE_FAST               6 (i)

164           LOAD_FAST_BORROW_LOAD_FAST_BORROW 6 (path_pts, i)
              BINARY_OP               26 ([])
              LOAD_SMALL_INT           0
              BINARY_OP               26 ([])
              LOAD_FAST_BORROW_LOAD_FAST_BORROW 6 (path_pts, i)
              LOAD_SMALL_INT           1
              BINARY_OP               10 (-)
              BINARY_OP               26 ([])
              LOAD_SMALL_INT           0
              BINARY_OP               26 ([])
              BINARY_OP               10 (-)
              STORE_FAST               7 (dx)

165           LOAD_FAST_BORROW_LOAD_FAST_BORROW 6 (path_pts, i)
              BINARY_OP               26 ([])
              LOAD_SMALL_INT           1
              BINARY_OP               26 ([])
              LOAD_FAST_BORROW_LOAD_FAST_BORROW 6 (path_pts, i)
              LOAD_SMALL_INT           1
              BINARY_OP               10 (-)
              BINARY_OP               26 ([])
              LOAD_SMALL_INT           1
              BINARY_OP               26 ([])
              BINARY_OP               10 (-)
              STORE_FAST               8 (dy)

166           LOAD_FAST_BORROW         5 (path_length)
              LOAD_GLOBAL              4 (math)
              LOAD_ATTR                6 (hypot)
              PUSH_NULL
              LOAD_FAST_BORROW_LOAD_FAST_BORROW 120 (dx, dy)
              CALL                     2
              BINARY_OP               13 (+=)
              STORE_FAST               5 (path_length)
              JUMP_BACKWARD          118 (to L2)

163   L3:     END_FOR
              POP_ITER

169           LOAD_GLOBAL              9 (max + NULL)
              LOAD_SMALL_INT           1
              LOAD_GLOBAL             11 (int + NULL)
              LOAD_GLOBAL              4 (math)
              LOAD_ATTR               12 (ceil)
              PUSH_NULL
              LOAD_FAST_BORROW_LOAD_FAST_BORROW 35 (pocket_depth, stepdown)
              BINARY_OP               11 (/)
              CALL                     1
              CALL                     1
              CALL                     2
              STORE_FAST               9 (pass_count)

172           LOAD_FAST_BORROW_LOAD_FAST_BORROW 89 (path_length, pass_count)
              BINARY_OP                5 (*)
              LOAD_FAST_BORROW         1 (feed_xy)
              BINARY_OP               11 (/)
              LOAD_SMALL_INT          60
              BINARY_OP                5 (*)
              STORE_FAST              10 (xy_time)

175           LOAD_FAST_BORROW_LOAD_FAST_BORROW 36 (pocket_depth, plunge_rate)
              BINARY_OP               11 (/)
              LOAD_SMALL_INT          60
              BINARY_OP                5 (*)
              STORE_FAST              11 (plunge_time)

178           LOAD_FAST_BORROW_LOAD_FAST_BORROW 171 (xy_time, plunge_time)
              BINARY_OP                0 (+)
              LOAD_CONST               2 (1.15)
              BINARY_OP                5 (*)
              STORE_FAST              12 (total)

180           LOAD_FAST_BORROW        12 (total)
              RETURN_VALUE

Disassembly of <code object __annotate__ at 0x0000024B1C70CC60, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 184>:
184           RESUME                   0
              LOAD_FAST_BORROW         0 (format)
              LOAD_SMALL_INT           2
              COMPARE_OP             132 (>)
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_COMMON_CONSTANT     1 (NotImplementedError)
              RAISE_VARARGS            1
      L1:     LOAD_CONST               1 ('intent')
              LOAD_CONST               2 ('CamIntentV1')
              LOAD_CONST               3 ('return')
              LOAD_CONST               4 ('PocketingIntentResponse')
              BUILD_MAP                2
              RETURN_VALUE

Disassembly of <code object generate_pocketing_intent_gcode at 0x0000024B1C5362D0, file "C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\cam\routers\pocketing\intent_router.py", line 183>:
 183            RETURN_GENERATOR
                POP_TOP
        L1:     RESUME                   0

 215            LOAD_GLOBAL              0 (HAS_FEASIBILITY)
                TO_BOOL
                POP_JUMP_IF_TRUE        18 (to L2)
                NOT_TAKEN

 216            LOAD_GLOBAL              3 (HTTPException + NULL)

 217            LOAD_CONST               1 (503)

 219            LOAD_CONST               2 ('error')
                LOAD_CONST               3 ('DEPENDENCY_UNAVAILABLE')

 220            LOAD_CONST               4 ('message')
                LOAD_CONST               5 ('Pocketing feasibility requires shapely which is not available (Python 3.14 numpy issue)')

 218            BUILD_MAP                2

 216            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

 223    L2:     LOAD_GLOBAL              4 (HAS_L1_CORE)
                TO_BOOL
                POP_JUMP_IF_TRUE        18 (to L5)
        L3:     NOT_TAKEN

 224    L4:     LOAD_GLOBAL              3 (HTTPException + NULL)

 225            LOAD_CONST               1 (503)

 227            LOAD_CONST               2 ('error')
                LOAD_CONST               3 ('DEPENDENCY_UNAVAILABLE')

 228            LOAD_CONST               4 ('message')
                LOAD_CONST               7 ('Pocketing requires L.1 adaptive core which is not available')

 226            BUILD_MAP                2

 224            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

 232    L5:     LOAD_GLOBAL              6 (datetime)
                LOAD_ATTR                8 (now)
                PUSH_NULL
                LOAD_GLOBAL             10 (timezone)
                LOAD_ATTR               12 (utc)
                CALL                     1
                LOAD_ATTR               15 (isoformat + NULL|self)
                CALL                     0
                STORE_FAST               1 (now)

 233            LOAD_GLOBAL             17 (sha256_of_obj + NULL)
                LOAD_FAST_BORROW         0 (intent)
                LOAD_ATTR               19 (model_dump + NULL|self)
                CALL                     0
                CALL                     1
                STORE_FAST               2 (request_hash)

 234            LOAD_FAST_BORROW         0 (intent)
                LOAD_ATTR               20 (tool_id)
                COPY                     1
                TO_BOOL
                POP_JUMP_IF_TRUE         3 (to L8)
        L6:     NOT_TAKEN
        L7:     POP_TOP
                LOAD_CONST               8 ('pocketing:intent')
        L8:     STORE_FAST               3 (tool_id)

 237    L9:     NOP

 238   L10:     LOAD_GLOBAL             23 (normalize_cam_intent_v1 + NULL)
                LOAD_FAST_BORROW         0 (intent)
                LOAD_CONST               9 (False)
                LOAD_CONST              10 (('strict',))
                CALL_KW                  2
                UNPACK_SEQUENCE          2
                STORE_FAST_STORE_FAST   69 (normalized, issues)

 250   L11:     LOAD_FAST                4 (normalized)
                LOAD_ATTR               36 (mode)
                LOAD_GLOBAL             38 (CamModeV1)
                LOAD_ATTR               40 (ROUTER_3AXIS)
                COMPARE_OP             119 (bool(!=))
                POP_JUMP_IF_FALSE       65 (to L12)
                NOT_TAKEN

 251            LOAD_GLOBAL              3 (HTTPException + NULL)

 252            LOAD_CONST              11 (422)

 254            LOAD_CONST               2 ('error')
                LOAD_CONST              17 ('INVALID_MODE')

 255            LOAD_CONST               4 ('message')
                LOAD_CONST              18 ('Pocketing requires mode=router_3axis, got ')
                LOAD_FAST                4 (normalized)
                LOAD_ATTR               36 (mode)
                LOAD_ATTR               42 (value)
                FORMAT_SIMPLE
                BUILD_STRING             2

 256            LOAD_CONST              19 ('expected')
                LOAD_CONST              20 ('router_3axis')

 257            LOAD_CONST              21 ('actual')
                LOAD_FAST                4 (normalized)
                LOAD_ATTR               36 (mode)
                LOAD_ATTR               42 (value)

 253            BUILD_MAP                4

 251            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

 262   L12:     NOP

 263   L13:     LOAD_GLOBAL             45 (validate_pocket_design + NULL)
                LOAD_FAST                4 (normalized)
                LOAD_ATTR               46 (design)
                CALL                     1
                STORE_FAST               8 (design)

 274   L14:     NOP

 275   L15:     LOAD_GLOBAL             51 (pocket_params_from_intent + NULL)
                LOAD_FAST                4 (normalized)
                CALL                     1
                STORE_FAST               9 (adaptation)

 286   L16:     LOAD_FAST                9 (adaptation)
                LOAD_ATTR               52 (loops)
                LOAD_SMALL_INT           0
                BINARY_OP               26 ([])
                STORE_FAST              10 (boundary)

 287            LOAD_GLOBAL             55 (len + NULL)
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               52 (loops)
                CALL                     1
                LOAD_SMALL_INT           1
                COMPARE_OP             148 (bool(>))
                POP_JUMP_IF_FALSE       20 (to L17)
                NOT_TAKEN
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               52 (loops)
                LOAD_CONST              24 (slice(1, None, None))
                BINARY_OP               26 ([])
                JUMP_FORWARD             1 (to L18)
       L17:     BUILD_LIST               0
       L18:     STORE_FAST              11 (islands)

 289            LOAD_GLOBAL             57 (compute_pocket_feasibility + NULL)

 290            LOAD_FAST               10 (boundary)

 291            LOAD_FAST               11 (islands)

 292            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               58 (pocket_depth_mm)

 293            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               60 (tool_d)

 294            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               62 (stepover)
                LOAD_SMALL_INT         100
                BINARY_OP                5 (*)

 295            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               64 (feed_xy)

 296            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               66 (plunge_rate)

 297            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               68 (safe_z)

 298            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               70 (retract_z)

 299            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               72 (stepdown)

 300            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               74 (finish_allowance_mm)

 289            LOAD_CONST              25 (('boundary', 'islands', 'pocket_depth_mm', 'tool_diameter_mm', 'stepover_percent', 'feed_rate_mm_min', 'plunge_rate_mm_min', 'safe_z_mm', 'retract_z_mm', 'stepdown_mm', 'finish_allowance_mm'))
                CALL_KW                 11
                STORE_FAST              12 (feasibility)

 302            LOAD_GLOBAL             77 (hash_feasibility_result + NULL)
                LOAD_FAST               12 (feasibility)
                CALL                     1
                STORE_FAST              13 (feas_hash)

 305            LOAD_FAST               12 (feasibility)
                LOAD_ATTR               78 (feasible)
                TO_BOOL
                POP_JUMP_IF_TRUE       179 (to L19)
                NOT_TAKEN

 306            LOAD_GLOBAL             81 (create_run_id + NULL)
                CALL                     0
                STORE_FAST              14 (run_id)

 307            LOAD_GLOBAL             83 (RunArtifact + NULL)

 308            LOAD_FAST               14 (run_id)

 309            LOAD_FAST                1 (now)

 310            LOAD_FAST                3 (tool_id)

 311            LOAD_CONST              26 ('pocketing_intent')

 312            LOAD_CONST              27 ('pocketing_intent_gcode_blocked')

 313            LOAD_CONST              28 ('BLOCKED')

 314            LOAD_FAST               12 (feasibility)
                LOAD_ATTR               85 (to_dict + NULL|self)
                CALL                     0

 315            LOAD_GLOBAL             87 (RunDecision + NULL)

 316            LOAD_FAST               12 (feasibility)
                LOAD_ATTR               88 (risk_level)

 317            LOAD_CONST              29 ('Blocked by feasibility check: ')
                LOAD_CONST              30 (', ')
                LOAD_ATTR               91 (join + NULL|self)
                LOAD_FAST               12 (feasibility)
                LOAD_ATTR               28 (issues)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             2

 315            LOAD_CONST              31 (('risk_level', 'block_reason'))
                CALL_KW                  2

 319            LOAD_GLOBAL             93 (Hashes + NULL)
                LOAD_FAST               13 (feas_hash)
                LOAD_CONST              32 (('feasibility_sha256',))
                CALL_KW                  1

 320            LOAD_CONST              33 ('Feasibility issues: ')
                LOAD_CONST              30 (', ')
                LOAD_ATTR               91 (join + NULL|self)
                LOAD_FAST               12 (feasibility)
                LOAD_ATTR               28 (issues)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             2

 307            LOAD_CONST              34 (('run_id', 'created_at_utc', 'tool_id', 'mode', 'event_type', 'status', 'feasibility', 'decision', 'hashes', 'notes'))
                CALL_KW                 10
                STORE_FAST              15 (artifact)

 322            LOAD_GLOBAL             95 (persist_run + NULL)
                LOAD_FAST               15 (artifact)
                CALL                     1
                POP_TOP

 324            LOAD_GLOBAL              3 (HTTPException + NULL)

 325            LOAD_CONST              35 (409)

 327            LOAD_CONST               2 ('error')
                LOAD_CONST              36 ('FEASIBILITY_BLOCKED')

 328            LOAD_CONST               4 ('message')
                LOAD_CONST              37 ('Pocketing G-code generation blocked by feasibility check.')

 329            LOAD_CONST              38 ('run_id')
                LOAD_FAST               14 (run_id)

 330            LOAD_CONST              39 ('feasibility')
                LOAD_FAST               12 (feasibility)
                LOAD_ATTR               85 (to_dict + NULL|self)
                CALL                     0

 326            BUILD_MAP                4

 324            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

 335   L19:     NOP

 336   L20:     LOAD_GLOBAL             97 (plan_adaptive_l1 + NULL)

 337            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               52 (loops)

 338            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               60 (tool_d)

 339            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               62 (stepover)

 340            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               72 (stepdown)

 341            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               98 (margin)

 342            LOAD_FAST                9 (adaptation)
                LOAD_ATTR              100 (strategy)

 343            LOAD_FAST                9 (adaptation)
                LOAD_ATTR              102 (smoothing_radius)

 336            LOAD_CONST              40 (('loops', 'tool_d', 'stepover', 'stepdown', 'margin', 'strategy', 'smoothing_radius'))
                CALL_KW                  7
                STORE_FAST              16 (path_pts)

 346            LOAD_FAST               16 (path_pts)
                TO_BOOL
                POP_JUMP_IF_TRUE        12 (to L21)
                NOT_TAKEN

 347            LOAD_GLOBAL             49 (ValueError + NULL)
                LOAD_CONST              41 ('L.1 returned empty toolpath')
                CALL                     1
                RAISE_VARARGS            1

 346   L21:     NOP

 376   L22:     NOP

 378   L23:     LOAD_GLOBAL            115 (max + NULL)
                LOAD_SMALL_INT           1
                LOAD_GLOBAL            117 (int + NULL)
                LOAD_GLOBAL            118 (math)
                LOAD_ATTR              120 (ceil)
                PUSH_NULL

 379            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               58 (pocket_depth_mm)
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               72 (stepdown)
                BINARY_OP               11 (/)

 378            CALL                     1
                CALL                     1
                CALL                     2
                STORE_FAST              17 (pass_count)

 383            LOAD_CONST              53 ('(Pocketing Operation - L.1 Adaptive Core)')

 384            LOAD_CONST              54 ('(Pocket depth: ')
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               58 (pocket_depth_mm)
                FORMAT_SIMPLE
                LOAD_CONST              55 ('mm in ')
                LOAD_FAST               17 (pass_count)
                FORMAT_SIMPLE
                LOAD_CONST              56 (' passes)')
                BUILD_STRING             5

 385            LOAD_CONST              57 ('(Tool: ')
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               60 (tool_d)
                FORMAT_SIMPLE
                LOAD_CONST              58 ('mm, Stepover: ')
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               62 (stepover)
                LOAD_SMALL_INT         100
                BINARY_OP                5 (*)
                LOAD_CONST              59 ('.0f')
                FORMAT_WITH_SPEC
                LOAD_CONST              60 ('%)')
                BUILD_STRING             5

 386            LOAD_CONST              61 ('(Islands: ')
                LOAD_GLOBAL             55 (len + NULL)
                LOAD_FAST               11 (islands)
                CALL                     1
                FORMAT_SIMPLE
                LOAD_CONST              62 (')')
                BUILD_STRING             3

 387            LOAD_CONST              63 ('')

 388            LOAD_CONST              64 ('G90 (Absolute positioning)')

 389            LOAD_CONST              65 ('G21 (Units: mm)')

 390            LOAD_CONST              66 ('M3 S18000 (Spindle on)')

 391            LOAD_CONST              67 ('G4 P2 (Dwell for spindle)')

 392            LOAD_CONST              68 ('G0 Z')
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               68 (safe_z)
                LOAD_CONST              69 ('.3f')
                FORMAT_WITH_SPEC
                LOAD_CONST              70 (' (Safe height)')
                BUILD_STRING             3

 393            LOAD_CONST              63 ('')

 382            BUILD_LIST              11
                STORE_FAST              18 (all_gcode_lines)

 396            LOAD_GLOBAL            123 (range + NULL)
                LOAD_SMALL_INT           1
                LOAD_FAST               17 (pass_count)
                LOAD_SMALL_INT           1
                BINARY_OP                0 (+)
                CALL                     2
                GET_ITER
       L24:     EXTENDED_ARG             1
                FOR_ITER               323 (to L31)
                STORE_FAST              19 (pass_num)

 397            LOAD_GLOBAL            125 (min + NULL)

 398            LOAD_FAST               19 (pass_num)
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               72 (stepdown)
                BINARY_OP                5 (*)

 399            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               58 (pocket_depth_mm)

 397            CALL                     2
                UNARY_NEGATIVE
                STORE_FAST              20 (z_depth)

 402            LOAD_FAST               18 (all_gcode_lines)
                LOAD_ATTR              127 (append + NULL|self)
                LOAD_CONST              71 ('(--- Pass ')
                LOAD_FAST               19 (pass_num)
                FORMAT_SIMPLE
                LOAD_CONST              72 (': Z = ')
                LOAD_FAST               20 (z_depth)
                LOAD_CONST              69 ('.3f')
                FORMAT_WITH_SPEC
                LOAD_CONST              73 (' ---)')
                BUILD_STRING             5
                CALL                     1
                POP_TOP

 404            LOAD_GLOBAL            129 (to_toolpath + NULL)

 405            LOAD_FAST               16 (path_pts)

 406            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               64 (feed_xy)

 407            LOAD_FAST               20 (z_depth)

 408            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               68 (safe_z)

 404            LOAD_CONST              74 (('path_pts', 'feed_xy', 'z_rough', 'safe_z'))
                CALL_KW                  4
                STORE_FAST              21 (moves)

 411            LOAD_FAST               21 (moves)
                GET_ITER
       L25:     FOR_ITER               196 (to L30)
                STORE_FAST              22 (move)

 412            LOAD_FAST               22 (move)
                LOAD_ATTR              131 (get + NULL|self)
                LOAD_CONST              14 ('code')
                LOAD_CONST              75 ('G1')
                CALL                     2
                STORE_FAST              23 (code)

 413            LOAD_FAST               23 (code)
                BUILD_LIST               1
                STORE_FAST              24 (parts)

 414            LOAD_CONST              76 ('x')
                LOAD_FAST               22 (move)
                CONTAINS_OP              0 (in)
                POP_JUMP_IF_FALSE       29 (to L26)
                NOT_TAKEN

 415            LOAD_FAST               24 (parts)
                LOAD_ATTR              127 (append + NULL|self)
                LOAD_CONST              77 ('X')
                LOAD_FAST               22 (move)
                LOAD_CONST              76 ('x')
                BINARY_OP               26 ([])
                LOAD_CONST              69 ('.3f')
                FORMAT_WITH_SPEC
                BUILD_STRING             2
                CALL                     1
                POP_TOP

 416   L26:     LOAD_CONST              78 ('y')
                LOAD_FAST               22 (move)
                CONTAINS_OP              0 (in)
                POP_JUMP_IF_FALSE       29 (to L27)
                NOT_TAKEN

 417            LOAD_FAST               24 (parts)
                LOAD_ATTR              127 (append + NULL|self)
                LOAD_CONST              79 ('Y')
                LOAD_FAST               22 (move)
                LOAD_CONST              78 ('y')
                BINARY_OP               26 ([])
                LOAD_CONST              69 ('.3f')
                FORMAT_WITH_SPEC
                BUILD_STRING             2
                CALL                     1
                POP_TOP

 418   L27:     LOAD_CONST              80 ('z')
                LOAD_FAST               22 (move)
                CONTAINS_OP              0 (in)
                POP_JUMP_IF_FALSE       29 (to L28)
                NOT_TAKEN

 419            LOAD_FAST               24 (parts)
                LOAD_ATTR              127 (append + NULL|self)
                LOAD_CONST              81 ('Z')
                LOAD_FAST               22 (move)
                LOAD_CONST              80 ('z')
                BINARY_OP               26 ([])
                LOAD_CONST              69 ('.3f')
                FORMAT_WITH_SPEC
                BUILD_STRING             2
                CALL                     1
                POP_TOP

 420   L28:     LOAD_CONST              82 ('f')
                LOAD_FAST               22 (move)
                CONTAINS_OP              0 (in)
                POP_JUMP_IF_FALSE       29 (to L29)
                NOT_TAKEN

 421            LOAD_FAST               24 (parts)
                LOAD_ATTR              127 (append + NULL|self)
                LOAD_CONST              83 ('F')
                LOAD_FAST               22 (move)
                LOAD_CONST              82 ('f')
                BINARY_OP               26 ([])
                LOAD_CONST              59 ('.0f')
                FORMAT_WITH_SPEC
                BUILD_STRING             2
                CALL                     1
                POP_TOP

 422   L29:     LOAD_FAST               18 (all_gcode_lines)
                LOAD_ATTR              127 (append + NULL|self)
                LOAD_CONST              84 (' ')
                LOAD_ATTR               91 (join + NULL|self)
                LOAD_FAST               24 (parts)
                CALL                     1
                CALL                     1
                POP_TOP
                JUMP_BACKWARD          198 (to L25)

 411   L30:     END_FOR
                POP_ITER

 424            LOAD_FAST               18 (all_gcode_lines)
                LOAD_ATTR              127 (append + NULL|self)
                LOAD_CONST              63 ('')
                CALL                     1
                POP_TOP
                EXTENDED_ARG             1
                JUMP_BACKWARD          326 (to L24)

 396   L31:     END_FOR
                POP_ITER

 426            LOAD_FAST               18 (all_gcode_lines)
                LOAD_ATTR              133 (extend + NULL|self)

 427            LOAD_CONST              68 ('G0 Z')
                LOAD_FAST                9 (adaptation)
                LOAD_ATTR               68 (safe_z)
                LOAD_CONST              69 ('.3f')
                FORMAT_WITH_SPEC
                LOAD_CONST              70 (' (Safe height)')
                BUILD_STRING             3

 428            LOAD_CONST              85 ('M5 (Spindle off)')

 429            LOAD_CONST              86 ('M30 (Program end)')

 426            BUILD_LIST               3
                CALL                     1
                POP_TOP

 432            LOAD_CONST              87 ('\n')
                LOAD_ATTR               91 (join + NULL|self)
                LOAD_FAST               18 (all_gcode_lines)
                CALL                     1
                STORE_FAST              25 (gcode)

 434            LOAD_FAST               25 (gcode)
                TO_BOOL
                POP_JUMP_IF_TRUE        12 (to L34)
       L32:     NOT_TAKEN

 435   L33:     LOAD_GLOBAL             49 (ValueError + NULL)
                LOAD_CONST              88 ('Generated G-code is empty')
                CALL                     1
                RAISE_VARARGS            1

 434   L34:     NOP

 464            LOAD_GLOBAL            135 (sha256_of_text + NULL)
                LOAD_FAST               25 (gcode)
                CALL                     1
                STORE_FAST              26 (gcode_hash)

 465            LOAD_GLOBAL             81 (create_run_id + NULL)
                CALL                     0
                STORE_FAST              14 (run_id)

 466            LOAD_GLOBAL             83 (RunArtifact + NULL)

 467            LOAD_FAST               14 (run_id)

 468            LOAD_FAST                1 (now)

 469            LOAD_FAST                3 (tool_id)

 470            LOAD_CONST              26 ('pocketing_intent')

 471            LOAD_CONST              45 ('pocketing_intent_gcode_execution')

 472            LOAD_CONST              92 ('OK')

 473            LOAD_FAST               12 (feasibility)
                LOAD_ATTR               85 (to_dict + NULL|self)
                CALL                     0

 474            LOAD_GLOBAL             87 (RunDecision + NULL)
                LOAD_FAST               12 (feasibility)
                LOAD_ATTR               88 (risk_level)
                LOAD_CONST              47 (('risk_level',))
                CALL_KW                  1

 475            LOAD_GLOBAL             93 (Hashes + NULL)

 476            LOAD_FAST               13 (feas_hash)

 477            LOAD_FAST               26 (gcode_hash)

 475            LOAD_CONST              93 (('feasibility_sha256', 'gcode_sha256'))
                CALL_KW                  2

 466            LOAD_CONST              94 (('run_id', 'created_at_utc', 'tool_id', 'mode', 'event_type', 'status', 'feasibility', 'decision', 'hashes'))
                CALL_KW                  9
                STORE_FAST              15 (artifact)

 480            LOAD_GLOBAL             95 (persist_run + NULL)
                LOAD_FAST               15 (artifact)
                CALL                     1
                POP_TOP

 483            LOAD_GLOBAL            137 (_estimate_time + NULL)

 484            LOAD_FAST               16 (path_pts)

 485            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               64 (feed_xy)

 486            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               58 (pocket_depth_mm)

 487            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               72 (stepdown)

 488            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               66 (plunge_rate)

 483            LOAD_CONST              95 (('path_pts', 'feed_xy', 'pocket_depth', 'stepdown', 'plunge_rate'))
                CALL_KW                  5
                STORE_FAST              27 (estimated_time)

 492            LOAD_GLOBAL            139 (PocketingIntentResponse + NULL)

 493            LOAD_FAST               25 (gcode)

 494            LOAD_GLOBAL            141 (_issues_to_response + NULL)
                LOAD_FAST                5 (issues)
                CALL                     1

 495            LOAD_FAST               14 (run_id)

 497            LOAD_CONST              96 ('request_sha256')
                LOAD_FAST                2 (request_hash)

 498            LOAD_CONST              97 ('feasibility_sha256')
                LOAD_FAST               13 (feas_hash)

 499            LOAD_CONST              98 ('gcode_sha256')
                LOAD_FAST               26 (gcode_hash)

 496            BUILD_MAP                3

 501            LOAD_GLOBAL            143 (PocketingIntentMetadata + NULL)

 502            LOAD_FAST               12 (feasibility)
                LOAD_ATTR              144 (summary)
                LOAD_ATTR              131 (get + NULL|self)
                LOAD_CONST              99 ('pocket_area_mm2')
                LOAD_CONST             100 (0.0)
                CALL                     2

 503            LOAD_GLOBAL             55 (len + NULL)
                LOAD_FAST               11 (islands)
                CALL                     1

 504            LOAD_FAST                9 (adaptation)
                LOAD_ATTR               62 (stepover)
                LOAD_SMALL_INT         100
                BINARY_OP                5 (*)

 505            LOAD_GLOBAL            147 (round + NULL)
                LOAD_FAST               27 (estimated_time)
                LOAD_SMALL_INT           1
                CALL                     2

 501            LOAD_CONST             101 (('pocket_area_mm2', 'island_count', 'stepover_percent', 'estimated_time_seconds'))
                CALL_KW                  4

 492            LOAD_CONST             102 (('gcode', 'issues', 'run_id', 'hashes', 'metadata'))
                CALL_KW                  5
                RETURN_VALUE

  --   L35:     PUSH_EXC_INFO

 239            LOAD_GLOBAL             24 (CamIntentValidationError)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE      102 (to L44)
                NOT_TAKEN
                STORE_FAST               6 (e)

 240   L36:     LOAD_GLOBAL              3 (HTTPException + NULL)

 241            LOAD_CONST              11 (422)

 243            LOAD_CONST               2 ('error')
                LOAD_CONST              12 ('NORMALIZATION_ERROR')

 244            LOAD_CONST               4 ('message')
                LOAD_GLOBAL             27 (str + NULL)
                LOAD_FAST                6 (e)
                CALL                     1

 245            LOAD_CONST              13 ('issues')
                LOAD_FAST                6 (e)
                LOAD_ATTR               28 (issues)
                GET_ITER
                LOAD_FAST_AND_CLEAR      7 (i)
                SWAP                     2
       L37:     BUILD_LIST               0
                SWAP                     2
       L38:     FOR_ITER                41 (to L39)
                STORE_FAST               7 (i)
                LOAD_CONST              14 ('code')
                LOAD_FAST                7 (i)
                LOAD_ATTR               30 (code)
                LOAD_CONST               4 ('message')
                LOAD_FAST                7 (i)
                LOAD_ATTR               32 (message)
                LOAD_CONST              15 ('path')
                LOAD_FAST                7 (i)
                LOAD_ATTR               34 (path)
                BUILD_MAP                3
                LIST_APPEND              2
                JUMP_BACKWARD           43 (to L38)
       L39:     END_FOR
                POP_ITER
       L40:     JUMP_FORWARD             5 (to L42)

  --   L41:     SWAP                     2
                POP_TOP

 245            SWAP                     2
                STORE_FAST               7 (i)
                RERAISE                  0
       L42:     SWAP                     2
                STORE_FAST               7 (i)

 242            BUILD_MAP                3

 240            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

  --   L43:     LOAD_CONST              16 (None)
                STORE_FAST               6 (e)
                DELETE_FAST              6 (e)
                RERAISE                  1

 239   L44:     RERAISE                  0

  --   L45:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
       L46:     PUSH_EXC_INFO

 264            LOAD_GLOBAL             48 (ValueError)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE       32 (to L49)
                NOT_TAKEN
                STORE_FAST               6 (e)

 265   L47:     LOAD_GLOBAL              3 (HTTPException + NULL)

 266            LOAD_CONST              11 (422)

 268            LOAD_CONST               2 ('error')
                LOAD_CONST              22 ('INVALID_DESIGN')

 269            LOAD_CONST               4 ('message')
                LOAD_GLOBAL             27 (str + NULL)
                LOAD_FAST                6 (e)
                CALL                     1

 267            BUILD_MAP                2

 265            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

  --   L48:     LOAD_CONST              16 (None)
                STORE_FAST               6 (e)
                DELETE_FAST              6 (e)
                RERAISE                  1

 264   L49:     RERAISE                  0

  --   L50:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
       L51:     PUSH_EXC_INFO

 276            LOAD_GLOBAL             48 (ValueError)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE       32 (to L54)
                NOT_TAKEN
                STORE_FAST               6 (e)

 277   L52:     LOAD_GLOBAL              3 (HTTPException + NULL)

 278            LOAD_CONST              11 (422)

 280            LOAD_CONST               2 ('error')
                LOAD_CONST              23 ('ADAPTER_ERROR')

 281            LOAD_CONST               4 ('message')
                LOAD_GLOBAL             27 (str + NULL)
                LOAD_FAST                6 (e)
                CALL                     1

 279            BUILD_MAP                2

 277            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

  --   L53:     LOAD_CONST              16 (None)
                STORE_FAST               6 (e)
                DELETE_FAST              6 (e)
                RERAISE                  1

 276   L54:     RERAISE                  0

  --   L55:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
       L56:     PUSH_EXC_INFO

 349            LOAD_GLOBAL            104 (Exception)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE      181 (to L59)
                NOT_TAKEN
                STORE_FAST               6 (e)

 350   L57:     LOAD_GLOBAL            106 (logger)
                LOAD_ATTR              109 (error + NULL|self)
                LOAD_CONST              42 ('L.1 toolpath generation failed: %s')
                LOAD_FAST                6 (e)
                LOAD_CONST              43 (True)
                LOAD_CONST              44 (('exc_info',))
                CALL_KW                  3
                POP_TOP

 351            LOAD_GLOBAL             81 (create_run_id + NULL)
                CALL                     0
                STORE_FAST              14 (run_id)

 352            LOAD_GLOBAL             83 (RunArtifact + NULL)

 353            LOAD_FAST               14 (run_id)

 354            LOAD_FAST                1 (now)

 355            LOAD_FAST                3 (tool_id)

 356            LOAD_CONST              26 ('pocketing_intent')

 357            LOAD_CONST              45 ('pocketing_intent_gcode_execution')

 358            LOAD_CONST              46 ('ERROR')

 359            LOAD_FAST               12 (feasibility)
                LOAD_ATTR               85 (to_dict + NULL|self)
                CALL                     0

 360            LOAD_GLOBAL             87 (RunDecision + NULL)
                LOAD_FAST               12 (feasibility)
                LOAD_ATTR               88 (risk_level)
                LOAD_CONST              47 (('risk_level',))
                CALL_KW                  1

 361            LOAD_GLOBAL             93 (Hashes + NULL)
                LOAD_FAST               13 (feas_hash)
                LOAD_CONST              32 (('feasibility_sha256',))
                CALL_KW                  1

 362            LOAD_GLOBAL            111 (type + NULL)
                LOAD_FAST                6 (e)
                CALL                     1
                LOAD_ATTR              112 (__name__)
                FORMAT_SIMPLE
                LOAD_CONST              48 (': ')
                LOAD_GLOBAL             27 (str + NULL)
                LOAD_FAST                6 (e)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             3
                BUILD_LIST               1

 352            LOAD_CONST              49 (('run_id', 'created_at_utc', 'tool_id', 'mode', 'event_type', 'status', 'feasibility', 'decision', 'hashes', 'errors'))
                CALL_KW                 10
                STORE_FAST              15 (artifact)

 364            LOAD_GLOBAL             95 (persist_run + NULL)
                LOAD_FAST               15 (artifact)
                CALL                     1
                POP_TOP

 366            LOAD_GLOBAL              3 (HTTPException + NULL)

 367            LOAD_CONST              50 (400)

 369            LOAD_CONST               2 ('error')
                LOAD_CONST              51 ('TOOLPATH_GENERATION_ERROR')

 370            LOAD_CONST              38 ('run_id')
                LOAD_FAST               14 (run_id)

 371            LOAD_CONST               4 ('message')
                LOAD_CONST              52 ('L.1 toolpath generation failed: ')
                LOAD_GLOBAL             27 (str + NULL)
                LOAD_FAST                6 (e)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             2

 368            BUILD_MAP                3

 366            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

  --   L58:     LOAD_CONST              16 (None)
                STORE_FAST               6 (e)
                DELETE_FAST              6 (e)
                RERAISE                  1

 349   L59:     RERAISE                  0

  --   L60:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
       L61:     PUSH_EXC_INFO

 437            LOAD_GLOBAL            104 (Exception)
                CHECK_EXC_MATCH
                POP_JUMP_IF_FALSE      181 (to L64)
                NOT_TAKEN
                STORE_FAST               6 (e)

 438   L62:     LOAD_GLOBAL            106 (logger)
                LOAD_ATTR              109 (error + NULL|self)
                LOAD_CONST              89 ('G-code generation failed: %s')
                LOAD_FAST                6 (e)
                LOAD_CONST              43 (True)
                LOAD_CONST              44 (('exc_info',))
                CALL_KW                  3
                POP_TOP

 439            LOAD_GLOBAL             81 (create_run_id + NULL)
                CALL                     0
                STORE_FAST              14 (run_id)

 440            LOAD_GLOBAL             83 (RunArtifact + NULL)

 441            LOAD_FAST               14 (run_id)

 442            LOAD_FAST                1 (now)

 443            LOAD_FAST                3 (tool_id)

 444            LOAD_CONST              26 ('pocketing_intent')

 445            LOAD_CONST              45 ('pocketing_intent_gcode_execution')

 446            LOAD_CONST              46 ('ERROR')

 447            LOAD_FAST               12 (feasibility)
                LOAD_ATTR               85 (to_dict + NULL|self)
                CALL                     0

 448            LOAD_GLOBAL             87 (RunDecision + NULL)
                LOAD_FAST               12 (feasibility)
                LOAD_ATTR               88 (risk_level)
                LOAD_CONST              47 (('risk_level',))
                CALL_KW                  1

 449            LOAD_GLOBAL             93 (Hashes + NULL)
                LOAD_FAST               13 (feas_hash)
                LOAD_CONST              32 (('feasibility_sha256',))
                CALL_KW                  1

 450            LOAD_GLOBAL            111 (type + NULL)
                LOAD_FAST                6 (e)
                CALL                     1
                LOAD_ATTR              112 (__name__)
                FORMAT_SIMPLE
                LOAD_CONST              48 (': ')
                LOAD_GLOBAL             27 (str + NULL)
                LOAD_FAST                6 (e)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             3
                BUILD_LIST               1

 440            LOAD_CONST              49 (('run_id', 'created_at_utc', 'tool_id', 'mode', 'event_type', 'status', 'feasibility', 'decision', 'hashes', 'errors'))
                CALL_KW                 10
                STORE_FAST              15 (artifact)

 452            LOAD_GLOBAL             95 (persist_run + NULL)
                LOAD_FAST               15 (artifact)
                CALL                     1
                POP_TOP

 454            LOAD_GLOBAL              3 (HTTPException + NULL)

 455            LOAD_CONST              50 (400)

 457            LOAD_CONST               2 ('error')
                LOAD_CONST              90 ('GCODE_GENERATION_ERROR')

 458            LOAD_CONST              38 ('run_id')
                LOAD_FAST               14 (run_id)

 459            LOAD_CONST               4 ('message')
                LOAD_CONST              91 ('G-code generation failed: ')
                LOAD_GLOBAL             27 (str + NULL)
                LOAD_FAST                6 (e)
                CALL                     1
                FORMAT_SIMPLE
                BUILD_STRING             2

 456            BUILD_MAP                3

 454            LOAD_CONST               6 (('status_code', 'detail'))
                CALL_KW                  2
                RAISE_VARARGS            1

  --   L63:     LOAD_CONST              16 (None)
                STORE_FAST               6 (e)
                DELETE_FAST              6 (e)
                RERAISE                  1

 437   L64:     RERAISE                  0

  --   L65:     COPY                     3
                POP_EXCEPT
                RERAISE                  1
       L66:     CALL_INTRINSIC_1         3 (INTRINSIC_STOPITERATION_ERROR)
                RERAISE                  1
ExceptionTable:
  L1 to L3 -> L66 [0] lasti
  L4 to L6 -> L66 [0] lasti
  L7 to L9 -> L66 [0] lasti
  L10 to L11 -> L35 [0]
  L11 to L12 -> L66 [0] lasti
  L13 to L14 -> L46 [0]
  L15 to L16 -> L51 [0]
  L16 to L19 -> L66 [0] lasti
  L20 to L21 -> L56 [0]
  L21 to L22 -> L66 [0] lasti
  L23 to L32 -> L61 [0]
  L33 to L34 -> L61 [0]
  L34 to L35 -> L66 [0] lasti
  L35 to L36 -> L45 [1] lasti
  L36 to L37 -> L43 [1] lasti
  L37 to L40 -> L41 [11]
  L40 to L43 -> L43 [1] lasti
  L43 to L45 -> L45 [1] lasti
  L45 to L46 -> L66 [0] lasti
  L46 to L47 -> L50 [1] lasti
  L47 to L48 -> L48 [1] lasti
  L48 to L50 -> L50 [1] lasti
  L50 to L51 -> L66 [0] lasti
  L51 to L52 -> L55 [1] lasti
  L52 to L53 -> L53 [1] lasti
  L53 to L55 -> L55 [1] lasti
  L55 to L56 -> L66 [0] lasti
  L56 to L57 -> L60 [1] lasti
  L57 to L58 -> L58 [1] lasti
  L58 to L60 -> L60 [1] lasti
  L60 to L61 -> L66 [0] lasti
  L61 to L62 -> L65 [1] lasti
  L62 to L63 -> L63 [1] lasti
  L63 to L65 -> L65 [1] lasti
  L65 to L66 -> L66 [0] lasti

```
---

## `cam/routers/pocketing/__init__`  
`app/cam/routers/pocketing/__pycache__/__init__.cpython-314.pyc` — 534 bytes, mtime(UTC) 2026-05-25T19:46:21.278192

### Recovered structure (names + string constants)
```
<<module>> names=['__doc__', 'intent_router', 'router', '__all__']
  str: 'router'
  str: 'intent_router'
```

### Full disassembly (`dis.dis`)
```
  0           RESUME                   0

  1           LOAD_CONST               0 ('\nCAM Pocketing Routers Package\n=============================\n\nPocketing operations using L.1 adaptive core.\n\nSub-modules:\n- intent_router.py (1 route: /intent-gcode) [CamIntentV1 - 8J]\n\nTotal: 1 route under /api/cam/pocketing\n')
              STORE_NAME               0 (__doc__)

 12           LOAD_SMALL_INT           1
              LOAD_CONST               1 (('router',))
              IMPORT_NAME              1 (intent_router)
              IMPORT_FROM              2 (router)
              STORE_NAME               1 (intent_router)
              POP_TOP

 15           LOAD_NAME                1 (intent_router)
              STORE_NAME               2 (router)

 18           LOAD_CONST               2 ('router')

 19           LOAD_CONST               3 ('intent_router')

 17           BUILD_LIST               2
              STORE_NAME               3 (__all__)
              LOAD_CONST               4 (None)
              RETURN_VALUE

```
---
