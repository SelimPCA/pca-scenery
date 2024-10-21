
The only YAML specific top level key is `variables` which can be used to create a list of aliases which can then be used in the other fields via the YAML anchor system.

```yaml
variables:
	-   &answer_data
		!common-item
		ID: INTERACTION_BASE
		interaction_ftype: radio_
		fragment_pos: 4
		fragment_id: 4

cases:
	CORRECT_RADIO:
		answer:
			<<: *answer_data
			radio_pos_and_flag: 1|20
			flag: 20
```