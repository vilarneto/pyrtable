#!/bin/bash


if [ -z "${AUTH_KEY}" ]; then
  echo "AUTH_KEY environment variable not set."
  exit 1
fi


EXECUTABLE="python3 -m tests.prepare_test_data -a ${AUTH_KEY}"


#$EXECUTABLE regioes
#$EXECUTABLE --page-size=10 uf
#$EXECUTABLE --filter-formula='{UF}="AM"' municipios
#$EXECUTABLE --filter-formula='OR({Porte}="Metrópole",{Porte}="Grande")' municipios
#$EXECUTABLE --filter-formula='{População 2010}>=200000' municipios
#$EXECUTABLE --filter-formula='AND({População 2010}>=150000,{População 2010}<=200000)' municipios
$EXECUTABLE --filter-formula='AND({Região}="Nordeste",{Porte}="Médio")' municipios
