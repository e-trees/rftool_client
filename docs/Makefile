quickguide.pdf: quickguide-cover.md operating_environment.md zcu111_setting.md awg-ja.md capture-ja.md digital-ja.md wave-sequence-vis-ja.md external-trigger-ja.md
	cat $^ | pandoc -f markdown -o $@ -V documentclass=ltjltxdoc -H preamble.tex --pdf-engine=lualatex --toc -N
