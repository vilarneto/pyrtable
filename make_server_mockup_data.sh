#!/bin/bash


if [ -z "${AUTH_KEY}" ]; then
  echo "AUTH_KEY environment variable not set."
  exit 1
fi


EXECUTABLE="python3 -m tests.prepare_test_data -a ${AUTH_KEY}"
STATE_FIELDS_OPT=--fields='Código,Nome'
REGION_FIELDS_OPT=--fields='Nome'
CITY_FIELDS_OPT=--fields='Nome,População 2010,Porte,Capital?'


#$EXECUTABLE municipios --record-id=recLyBCK45O1od8Li
#$EXECUTABLE municipios --record-id=rec1bjgfb5qTHfEeX
#$EXECUTABLE municipios --record-id=rec00000000000000  # nonexistent

#$EXECUTABLE regioes --record-id=recf3tnhMRerrI2s9
#$EXECUTABLE regioes --record-id=rec00000000000000  # nonexistent

#$EXECUTABLE $CITY_FIELDS_OPT --filter-formula='({Capital?})' municipios

#$EXECUTABLE $REGION_FIELDS_OPT regioes

#$EXECUTABLE $STATE_FIELDS_OPT --page-size=10 uf

#$EXECUTABLE $CITY_FIELDS_OPT --filter-formula='({Capital?})' municipios
#$EXECUTABLE $CITY_FIELDS_OPT --filter-formula='{Nome}="Bom Jesus"' municipios

#$EXECUTABLE $CITY_FIELDS_OPT --filter-formula='{UF}="AM"' municipios
#$EXECUTABLE $CITY_FIELDS_OPT --filter-formula='OR({Porte}="Metrópole",{Porte}="Grande")' municipios
#$EXECUTABLE $CITY_FIELDS_OPT --filter-formula='{População 2010}>=200000' municipios
#$EXECUTABLE $CITY_FIELDS_OPT --filter-formula='AND({População 2010}>=150000,{População 2010}<=200000)' municipios
#$EXECUTABLE $CITY_FIELDS_OPT --filter-formula='AND({Região}="Nordeste",{Porte}="Médio")' municipios

RECORD_ID=$($EXECUTABLE --method=POST \
    --json-data="{\"records\": [{\"fields\": {\"Nome\": \"(test)\", \"População 2010\": 12345, \"Porte\": \"Médio\"}}]}" \
    --print-records-ids \
    municipios)
$EXECUTABLE --method=DELETE --record-id="${RECORD_ID}" municipios

#$EXECUTABLE --method=DELETE \
#    --json-data="{\"records\": [\"${RECORD_ID}\"]}" \
#    municipios
