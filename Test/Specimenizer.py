#MenuTitle: Specimenizer
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__="""
Creates a self-contained HTML type specimen for the current font (or Glyphs project) inside the current Webfont Export folder: cover, style overview, waterfall, sample paragraphs, character set, OpenType feature comparisons, and variable axis sliders.
"""

from GlyphsApp import *
from AppKit import NSBundle, NSClassFromString
from os import system
import codecs, datetime

waterfallSizes = (120, 96, 72, 60, 48, 36, 24, 18, 14, 12, 10, 8)
paragraphSizes = (24, 16, 11, 8)

defaultSampleLine = "Hamburgefonstiv"
defaultParagraph = "Jaded zombies acted quaintly but kept driving their oxen forward. The quick brown fox jumps over the lazy dog, while five wizards vex the gnome. 0123456789 — “Typography is the craft of endowing human language with a durable visual form.”"

# sample strings per OT feature, fallback is the paragraph sample:
featureSamples = {
	"smcp": "Small Caps Are Not Capitals",
	"c2sc": "SMALL CAPS FROM CAPITALS",
	"pcap": "Petite Caps Sample Text",
	"c2pc": "PETITE CAPS FROM CAPITALS",
	"onum": "Prices 0123456789 in 1867",
	"lnum": "Prices 0123456789 in 1867",
	"tnum": "0123456789 11111 00000",
	"pnum": "0123456789 11111 00000",
	"zero": "0 1000 0.05 100,000",
	"frac": "1/2 3/4 5/8 21/100",
	"sups": "1st 2nd 3rd 4th M12",
	"subs": "H2O CO2 C6H12O6",
	"numr": "12/34 56/78",
	"dnom": "12/34 56/78",
	"sinf": "H2O CO2 C6H12O6",
	"ordn": "No 1a 2o 3er 4me",
	"liga": "fi fl ffi ffl ff office waffle",
	"dlig": "st ct sp Th ffj waffle",
	"hlig": "st ct sp Th ffj waffle",
	"clig": "waffle office affluent",
	"calt": "AVATAR ///// \\\\\\\\\\ ..!?",
	"case": "(HAMBURG) ¡ALTO! ¿QUÉ? H-H",
	"cpsp": "SPACED OUT CAPITALS",
	"titl": "TITLING CAPITALS SET",
	"swsh": "Answer Quickly, Zorro",
	"salt": "Alternate Glyph Shapes 1234",
	"kern": "AVATAR Ty. Wo Yo P, LT",
	"unic": "Unicase Sample Text",
	"hist": "Historical Substitution",
	"rvrn": "Required Variation Alternates",
}

def saveFileInLocation( content="Sorry, no content generated.", fileName="specimen.html", filePath="~/Desktop" ):
	saveFileLocation = "%s/%s" % (filePath, fileName)
	saveFileLocation = saveFileLocation.replace( "//", "/" )
	with codecs.open(saveFileLocation, "w", "utf-8-sig") as thisFile:
		print("  💾 Exporting to: %s" % thisFile.name)
		thisFile.write( content )
		thisFile.close()
	return True

def replaceSet( text, setOfReplacements ):
	for thisReplacement in setOfReplacements:
		searchFor = thisReplacement[0]
		replaceWith = thisReplacement[1]
		text = text.replace( searchFor, replaceWith )
	return text

def escapeHTML( text ):
	if not text:
		return ""
	return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def escapeJS( text ):
	if not text:
		return ""
	return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

def currentFileFormats():
	if Glyphs.versionNumber < 3.0:
		# GLYPHS 2
		return ("woff2", "woff")
	# GLYPHS 3
	fileFormats = []
	if Glyphs.defaults["OTFExportWOFF2"]:
		fileFormats.append("woff2")
	if Glyphs.defaults["OTFExportWOFF"]:
		fileFormats.append("woff")
	if Glyphs.defaults["OTFExportPlain"]:
		if Glyphs.defaults["OTFExportOutlineformat"] == 2: # TTF
			fileFormats.append("ttf")
		else:
			fileFormats.append("otf")
	if not fileFormats:
		fileFormats = ["woff2"]
	return tuple(fileFormats)

def currentWebExportPath():
	if Glyphs.versionNumber < 3.0:
		# GLYPHS 2
		exportPath = Glyphs.defaults["WebfontPluginExportPathManual"]
		if Glyphs.defaults["WebfontPluginUseExportPath"]:
			exportPath = Glyphs.defaults["WebfontPluginExportPath"]
	else:
		# GLYPHS 3
		exportPath = Glyphs.defaults["OTFExportPathManual"]
		if Glyphs.defaults["OTFExportUseExportPath"]:
			exportPath = Glyphs.defaults["OTFExportPath"]
	return exportPath

def isSingleInstance( instance ):
	if Glyphs.versionNumber >= 3:
		# GLYPHS 3
		return instance.type == INSTANCETYPESINGLE
	else:
		# GLYPHS 2
		return True

def isVariableInstance( instance ):
	if Glyphs.versionNumber < 3:
		return False
	try:
		return instance.type == INSTANCETYPEVARIABLE
	except:
		return False

def instanceFileName( thisFont, thisInstance, fileFormat ):
	familyName = thisInstance.customParameters["familyName"]
	if not familyName:
		familyName = thisFont.familyName
	fileNameOfInstance = thisInstance.fileName()
	firstPartOfFileName = ""
	if fileNameOfInstance:
		firstPartOfFileName = ".".join( fileNameOfInstance.split(".")[:-1] ) # removes ".otf" at the end
	if not firstPartOfFileName:
		firstPartOfFileName = thisInstance.customParameters["fileName"]
	if not firstPartOfFileName:
		firstPartOfFileName = "%s-%s" % ( familyName.replace(" ",""), thisInstance.name.replace(" ","") )
	return "%s.%s" % ( firstPartOfFileName, fileFormat )

def instanceCSSName( thisFont, thisInstance, fileFormat ):
	familyName = thisInstance.customParameters["familyName"]
	if not familyName:
		familyName = thisFont.familyName
	return "%s %s %s" % ( fileFormat.upper(), familyName, thisInstance.name )

def singleInstances( thisFont, thisProject=None ):
	if thisProject:
		instances = thisProject.instances()
	else:
		instances = thisFont.instances
	return [i for i in instances if i.active and isSingleInstance(i)]

def variableInstances( thisFont, thisProject=None ):
	if thisProject:
		instances = thisProject.instances()
	else:
		instances = thisFont.instances
	return [i for i in instances if i.active and isVariableInstance(i)]

def instanceInfos( thisFont, instances, fileFormat ):
	"""Returns a tuple of (fileName, cssName, styleName) for every instance."""
	infos = []
	for thisInstance in instances:
		infos.append((
			instanceFileName( thisFont, thisInstance, fileFormat ),
			instanceCSSName( thisFont, thisInstance, fileFormat ),
			thisInstance.name,
		))
	return tuple(infos)

def fontFaces( instanceInfoList, isVariable=False, axisInfos=() ):
	code = ""
	for fileName, cssName, styleName in instanceInfoList:
		code += "\t\t@font-face {\n\t\t\tfont-family: '%s';\n\t\t\tsrc: url('%s');\n" % ( cssName, fileName )
		if isVariable and axisInfos:
			for tag, name, minimum, maximum, default in axisInfos:
				if tag == "wght":
					code += "\t\t\tfont-weight: %i %i;\n" % ( minimum, maximum )
				elif tag == "wdth":
					code += "\t\t\tfont-stretch: %i%% %i%%;\n" % ( minimum, maximum )
		code += "\t\t}\n"
	return code

def optionList( instanceInfoList ):
	code = ""
	for fileName, cssName, styleName in instanceInfoList:
		code += '\t\t\t<option value="%s">%s</option>\n' % ( escapeHTML(cssName), escapeHTML(styleName) )
	return code

def styleSections( instanceInfoList ):
	code = ""
	for fileName, cssName, styleName in instanceInfoList:
		code += '\t\t<div class="styleRow">\n'
		code += '\t\t\t<div class="styleName">%s</div>\n' % escapeHTML(styleName)
		code += '\t\t\t<div class="styleSample sampleLine" style="font-family: \'%s\';"></div>\n' % escapeHTML(cssName)
		code += '\t\t</div>\n'
	return code

def waterfallLines():
	code = ""
	for size in waterfallSizes:
		code += '\t\t<p class="waterfallLine"><span class="sizeLabel">%i</span><span class="sampleLine specimenText" style="font-size: %ipx;"></span></p>\n' % ( size, size )
	return code

def paragraphColumns():
	code = ""
	for size in paragraphSizes:
		code += '\t\t<div class="paragraphBlock">\n'
		code += '\t\t\t<div class="sizeLabel">%ipx</div>\n' % size
		code += '\t\t\t<p class="sampleParagraph specimenText" style="font-size: %ipx; line-height: %.2f;"></p>\n' % ( size, 1.15 + 12.0/size*0.15 )
		code += '\t\t</div>\n'
	return code

def characterSet( thisFont ):
	"""Grid of all exporting, encoded glyphs. Marks get a dotted circle."""
	code = ""
	glyphCount = 0
	for thisGlyph in thisFont.glyphs:
		if not thisGlyph.export or not thisGlyph.unicode:
			continue
		glyphCount += 1
		character = "&#x%s;" % thisGlyph.unicode
		if thisGlyph.subCategory == "Nonspacing":
			character = "&#x25CC;%s" % character
		code += '\t\t<div class="glyphCell" title="%s">\n' % escapeHTML(thisGlyph.name)
		code += '\t\t\t<div class="glyphBox specimenText">%s</div>\n' % character
		code += '\t\t\t<div class="glyphInfo">%s</div>\n' % thisGlyph.unicode
		code += '\t\t</div>\n'
	return code, glyphCount

def exportingFeatures( thisFont ):
	features = []
	doneFeatures = []
	for thisFeature in thisFont.features:
		featureName = thisFeature.name
		if featureName in doneFeatures:
			continue
		try:
			if thisFeature.disabled():
				continue
		except:
			pass
		doneFeatures.append(featureName)
		featureLabel = ""
		notes = thisFeature.notes
		if featureName.startswith("ss") and notes and notes.startswith("Name:"):
			featureLabel = notes.splitlines()[0][5:].strip()
		features.append( (featureName, featureLabel) )
	return features

def featureToggles( features ):
	code = ""
	defaultOn = ("kern", "liga", "clig", "calt", "ccmp", "locl", "rlig", "mark", "mkmk")
	# kerning and default features are not necessarily listed in Font Info > Features:
	featureNames = [f[0] for f in features]
	toggleFeatures = [(f, "") for f in ("kern", "liga", "clig", "calt") if not f in featureNames]
	toggleFeatures += [f for f in features if f[0] != "aalt"]
	for featureName, featureLabel in toggleFeatures:
		checked = " checked" if featureName in defaultOn else ""
		labelContent = escapeHTML(featureName)
		if featureLabel:
			labelContent += '<span class="tooltip">%s</span>' % escapeHTML(featureLabel)
		code += '\t\t<input type="checkbox" id="%s" value="%s" class="otFeature" onchange="updateFeatures()"%s><label for="%s" class="otFeatureLabel">%s</label>\n' % (
			featureName, featureName, checked, featureName, labelContent
		)
	return code

def featureComparisons( features ):
	"""Before/after rows for all features that are not on by default."""
	code = ""
	skip = ("ccmp", "locl", "mark", "mkmk", "rlig", "aalt", "rvrn")
	for featureName, featureLabel in features:
		if featureName in skip:
			continue
		sample = featureSamples.get( featureName, defaultSampleLine )
		if featureName.startswith("ss") or featureName.startswith("cv"):
			sample = featureSamples.get( "salt", defaultSampleLine )
		title = escapeHTML(featureName)
		if featureLabel:
			title += ' <span class="featureDescription">%s</span>' % escapeHTML(featureLabel)
		code += '\t\t<div class="featureRow">\n'
		code += '\t\t\t<div class="featureTag">%s</div>\n' % title
		code += '\t\t\t<div class="featureSample specimenText featureOff">%s</div>\n' % escapeHTML(sample)
		code += '\t\t\t<div class="featureSample specimenText" style="font-feature-settings: \'%s\' on;">%s</div>\n' % ( featureName, escapeHTML(sample) )
		code += '\t\t</div>\n'
	return code

def axisInfosOfFont( thisFont ):
	"""Returns a tuple of (tag, name, minimum, maximum, default) for every axis, in user coordinates where available."""
	if Glyphs.versionNumber < 3:
		return ()
	axisInfos = []
	instances = singleInstances( thisFont )
	for axisIndex, thisAxis in enumerate(thisFont.axes):
		values = []
		# user coordinates, if the instances carry Axis Location parameters:
		for thisInstance in instances:
			axisLocation = thisInstance.customParameters["Axis Location"]
			if axisLocation:
				for entry in axisLocation:
					if entry["Axis"] == thisAxis.name:
						values.append( float(entry["Location"]) )
		if not values:
			# fall back on design coordinates:
			for thisMaster in thisFont.masters:
				try:
					values.append( float(thisMaster.axes[axisIndex]) )
				except:
					pass
			for thisInstance in instances:
				try:
					values.append( float(thisInstance.axes[axisIndex]) )
				except:
					pass
		if not values:
			continue
		minimum, maximum = min(values), max(values)
		if minimum == maximum:
			continue
		axisTag = thisAxis.axisTag
		default = minimum
		for preferredDefault in ( {"wght":400.0, "wdth":100.0, "slnt":0.0, "ital":0.0, "opsz":12.0}.get(axisTag, None), ):
			if preferredDefault is not None and minimum <= preferredDefault <= maximum:
				default = preferredDefault
		axisInfos.append( (axisTag, thisAxis.name, minimum, maximum, default) )
	return tuple(axisInfos)

def axisSliders( axisInfos ):
	code = ""
	for tag, name, minimum, maximum, default in axisInfos:
		step = 1
		if maximum - minimum < 20:
			step = 0.1
		code += '\t\t<div class="axisRow">\n'
		code += '\t\t\t<label class="axisName" for="axis_%s">%s <span class="axisTag">%s</span></label>\n' % ( tag, escapeHTML(name), escapeHTML(tag) )
		code += '\t\t\t<input type="range" id="axis_%s" data-tag="%s" class="axisSlider" min="%g" max="%g" step="%g" value="%g" oninput="updateVariations()">\n' % ( tag, tag, minimum, maximum, step, default )
		code += '\t\t\t<output id="axisValue_%s">%g</output>\n' % ( tag, default )
		code += '\t\t</div>\n'
	return code

htmlContent = """<!DOCTYPE html>
<html lang="en">
<head>
	<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>{{familyName}} Specimen</title>
	<style type="text/css">
{{fontFaces}}
		:root {
			--fg: #111;
			--bg: #fff;
			--dim: #888;
			--rule: #ddd;
			--chrome: #f2f2f2;
		}
		@media (prefers-color-scheme: dark) {
			:root {
				--fg: #f0f0f0;
				--bg: #1c1c1c;
				--dim: #999;
				--rule: #3a3a3a;
				--chrome: #262626;
			}
		}
		* { box-sizing: border-box; }
		body {
			margin: 0;
			padding: 0 0 6em 0;
			background: var(--bg);
			color: var(--fg);
			font: normal normal normal 13px/1.4 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
		}
		#controls {
			position: sticky;
			top: 0;
			z-index: 10;
			background: var(--chrome);
			border-bottom: 1px solid var(--rule);
			padding: 0.6em 1.2em;
			user-select: none;
			-webkit-user-select: none;
		}
		#controls .row {
			display: flex;
			flex-wrap: wrap;
			align-items: center;
			gap: 0.5em;
			margin-bottom: 0.4em;
		}
		#controls .row:last-child { margin-bottom: 0; }
		#textInput {
			flex: 1 1 20em;
			min-width: 12em;
			border: 1px solid var(--rule);
			background: var(--bg);
			color: var(--fg);
			padding: 0.3em 0.5em;
			font: inherit;
		}
		select, button {
			background: var(--bg);
			color: var(--fg);
			border: 1px solid var(--rule);
			padding: 0.3em 0.5em;
			font: inherit;
		}
		button { cursor: pointer; }
		.otFeature {
			position: absolute;
			opacity: 0;
			pointer-events: none;
		}
		.otFeatureLabel {
			position: relative;
			display: inline-block;
			color: var(--dim);
			background: var(--bg);
			border: 1px solid var(--rule);
			border-radius: 0.3em;
			padding: 0.15em 0.5em 0.25em 0.5em;
			cursor: pointer;
			white-space: nowrap;
		}
		.otFeature:checked + .otFeatureLabel {
			color: var(--bg);
			background: var(--fg);
			border-color: var(--fg);
		}
		.otFeatureLabel .tooltip {
			visibility: hidden;
			position: absolute;
			left: 0;
			bottom: 1.9em;
			background: #333;
			color: #fff;
			padding: 0 0.4em;
			border-radius: 0.2em;
			white-space: nowrap;
			z-index: 12;
		}
		.otFeatureLabel:hover .tooltip { visibility: visible; }

		article { padding: 0 1.2em; max-width: 100%; }
		section { border-top: 1px solid var(--rule); padding: 1.6em 0; }
		h2 {
			font: inherit;
			text-transform: uppercase;
			letter-spacing: 0.12em;
			color: var(--dim);
			margin: 0 0 1em 0;
		}
		header#cover { padding: 2em 0 1.5em 0; }
		#coverLine {
			font-family: '{{firstFontName}}';
			font-size: 12vw;
			line-height: 1;
			margin: 0 0 0.3em 0;
			word-wrap: break-word;
		}
		#coverMeta { color: var(--dim); }
		#coverMeta span::after { content: " · "; }
		#coverMeta span:last-child::after { content: ""; }

		.styleRow {
			display: flex;
			align-items: baseline;
			gap: 1em;
			border-bottom: 1px solid var(--rule);
			padding: 0.5em 0;
			overflow: hidden;
		}
		.styleRow:last-child { border-bottom: 0; }
		.styleName {
			flex: 0 0 12em;
			color: var(--dim);
		}
		.styleSample {
			flex: 1 1 auto;
			font-size: 36px;
			line-height: 1.1;
			white-space: nowrap;
			overflow: hidden;
		}

		.waterfallLine {
			margin: 0 0 0.25em 0;
			display: flex;
			align-items: baseline;
			gap: 0.8em;
			overflow: hidden;
		}
		.sizeLabel {
			flex: 0 0 3em;
			color: var(--dim);
			font-size: 11px;
			text-align: right;
		}
		.waterfallLine .sampleLine {
			flex: 1 1 auto;
			white-space: nowrap;
			overflow: hidden;
			line-height: 1.1;
		}

		#paragraphs { display: flex; flex-wrap: wrap; gap: 1.5em; }
		.paragraphBlock { flex: 1 1 18em; min-width: 15em; }
		.paragraphBlock .sizeLabel { text-align: left; margin-bottom: 0.4em; }
		.sampleParagraph { margin: 0; text-align: justify; hyphens: auto; }

		#charset {
			display: grid;
			grid-template-columns: repeat(auto-fill, minmax(3.6em, 1fr));
			gap: 1px;
			background: var(--rule);
			border: 1px solid var(--rule);
		}
		#charset h2 { grid-column: 1 / -1; background: var(--bg); padding-top: 1.6em; border: 0; }
		.glyphCell { background: var(--bg); padding: 0.3em 0.1em; text-align: center; }
		.glyphBox { font-size: 26px; line-height: 1.3; }
		.glyphInfo { color: var(--dim); font-size: 9px; }

		.featureRow {
			display: flex;
			align-items: baseline;
			gap: 1em;
			padding: 0.4em 0;
			border-bottom: 1px solid var(--rule);
			overflow: hidden;
		}
		.featureTag { flex: 0 0 10em; color: var(--dim); }
		.featureDescription { display: block; font-size: 11px; }
		.featureSample {
			flex: 1 1 0;
			font-size: 28px;
			line-height: 1.2;
			white-space: nowrap;
			overflow: hidden;
		}
		.featureOff {
			color: var(--dim);
			font-feature-settings: "liga" off, "calt" off, "clig" off;
		}

		.axisRow { display: flex; align-items: center; gap: 0.8em; margin-bottom: 0.5em; }
		.axisName { flex: 0 0 12em; }
		.axisTag { color: var(--dim); }
		.axisSlider { flex: 1 1 auto; }
		output { flex: 0 0 4em; color: var(--dim); }
		#variableSample {
			font-family: '{{firstVariableFontName}}';
			font-size: 64px;
			line-height: 1.15;
			margin-top: 0.6em;
			word-wrap: break-word;
		}

		footer {
			border-top: 1px solid var(--rule);
			padding: 1.5em 0;
			color: var(--dim);
			font-size: 11px;
		}
		.inverted { background: var(--fg); color: var(--bg); }
		.inverted .specimenText, .inverted .styleSample { color: var(--bg); }

		@media print {
			#controls { display: none; }
			body { background: #fff; color: #000; padding-bottom: 0; }
			section { break-inside: avoid; }
		}
	</style>
</head>
<body>
<div id="controls">
	<div class="row">
		<select id="fontFamilySelector" onchange="changeFont()">
{{optionList}}
		</select>
		<input type="text" id="textInput" value="{{sampleLine}}" onclick="this.select();" oninput="updateSample()" spellcheck="false" />
		<button onclick="resetSample()">Reset</button>
		<button onclick="toggleInverse()">Invert</button>
		<button onclick="window.print()">Print</button>
	</div>
	<div class="row" id="featureLine">
{{featureToggles}}
	</div>
</div>

<article id="specimen">
	<header id="cover">
		<h1 id="coverLine" class="sampleLine specimenText"></h1>
		<p id="coverMeta">
			<span>{{styleCount}} styles</span>
			<span>{{glyphCount}} glyphs</span>
{{coverMeta}}
		</p>
	</header>

	<section id="styles">
		<h2>Styles</h2>
{{styleSections}}
	</section>

	<section id="waterfall">
		<h2>Waterfall</h2>
{{waterfallLines}}
	</section>

	<section id="paragraphs">
		<h2 style="flex: 1 0 100%;">Text Sizes</h2>
{{paragraphColumns}}
	</section>

	<section id="charset">
		<h2>Character Set</h2>
{{characterSet}}
	</section>

	<section id="features">
		<h2>OpenType Features — off / on</h2>
{{featureComparisons}}
	</section>

{{variableSection}}

	<footer>
		<p>{{copyright}}</p>
		<p>Specimen generated with the Specimenizer script from the mekkablue scripts on {{date}}.</p>
	</footer>
</article>

<script type="text/javascript">
	const defaultSampleLine = document.getElementById("textInput").value;
	const defaultParagraph = "{{sampleParagraph}}";
	const selector = document.getElementById("fontFamilySelector");

	function updateSample() {
		const text = document.getElementById("textInput").value;
		const lines = document.getElementsByClassName("sampleLine");
		for (let i = 0; i < lines.length; i++) {
			lines[i].textContent = text;
		}
		const paragraphs = document.getElementsByClassName("sampleParagraph");
		const paragraphText = (text == defaultSampleLine) ? defaultParagraph : text;
		for (let i = 0; i < paragraphs.length; i++) {
			paragraphs[i].textContent = paragraphText;
		}
	}
	function resetSample() {
		document.getElementById("textInput").value = defaultSampleLine;
		updateSample();
	}
	function changeFont() {
		const fontName = selector.options[selector.selectedIndex].value;
		const elements = document.getElementsByClassName("specimenText");
		for (let i = 0; i < elements.length; i++) {
			elements[i].style.fontFamily = "'" + fontName + "'";
		}
	}
	function updateFeatures() {
		const checkboxes = document.getElementsByClassName("otFeature");
		let settings = [];
		for (let i = 0; i < checkboxes.length; i++) {
			settings.push('"' + checkboxes[i].value + '" ' + (checkboxes[i].checked ? "on" : "off"));
		}
		const code = settings.join(", ");
		const elements = document.getElementsByClassName("specimenText");
		for (let i = 0; i < elements.length; i++) {
			if (!elements[i].classList.contains("featureSample")) {
				elements[i].style.fontFeatureSettings = code;
			}
		}
	}
	function updateVariations() {
		const sliders = document.getElementsByClassName("axisSlider");
		let settings = [];
		for (let i = 0; i < sliders.length; i++) {
			settings.push('"' + sliders[i].dataset.tag + '" ' + sliders[i].value);
			const readout = document.getElementById("axisValue_" + sliders[i].dataset.tag);
			if (readout) {
				readout.value = sliders[i].value;
			}
		}
		const sample = document.getElementById("variableSample");
		if (sample) {
			sample.style.fontVariationSettings = settings.join(", ");
		}
	}
	function toggleInverse() {
		document.body.classList.toggle("inverted");
	}
	document.addEventListener("keyup", function(event) {
		if (!event.ctrlKey) return;
		if (event.code == "Period") {
			selector.selectedIndex = (selector.selectedIndex + 1) % selector.options.length;
			changeFont();
		} else if (event.code == "Comma") {
			selector.selectedIndex = (selector.selectedIndex + selector.options.length - 1) % selector.options.length;
			changeFont();
		} else if (event.code == "KeyR") {
			resetSample();
		}
	});

	updateSample();
	changeFont();
	updateFeatures();
	updateVariations();
</script>
</body>
</html>
"""

variableSectionContent = """	<section id="variable">
		<h2>Variable Axes</h2>
{{axisSliders}}
		<div id="variableSample" class="sampleLine"></div>
	</section>
"""

# brings macro window to front and clears its log:
Glyphs.clearLog()

# Query app version:
GLYPHSAPPVERSION = NSBundle.bundleForClass_(NSClassFromString("GSMenu")).infoDictionary().objectForKey_("CFBundleShortVersionString")
appVersionHighEnough = not GLYPHSAPPVERSION.startswith("1.")

if not appVersionHighEnough:
	print("❌ This script requires Glyphs 2 or higher. Sorry.")
elif not Glyphs.orderedDocuments():
	Message(
		title="⚠️ No font open",
		message="Specimenizer requires an open font or project file.",
		OKButton=None,
	)
	print("❌ No document open. Aborting.")
else:
	firstDoc = Glyphs.orderedDocuments()[0]
	thisProject = None
	if firstDoc.isKindOfClass_(GSProjectDocument):
		# frontmost doc is a .glyphsproject file:
		thisFont = firstDoc.font()
		thisProject = firstDoc
		exportPath = firstDoc.exportPath()
	else:
		# frontmost doc is a .glyphs file:
		thisFont = Glyphs.font
		exportPath = currentWebExportPath()

	familyName = thisFont.familyName
	print("Specimenizer report for %s:" % familyName)

	fileFormat = currentFileFormats()[0]
	instances = singleInstances( thisFont, thisProject )

	if not instances:
		exports = "Exports" if Glyphs.versionNumber >= 3 else "Instances"
		Message(
			title="⚠️ No exporting fonts found",
			message="No active font instances are set in Font Info > %s. Cannot create a specimen for %s." % (exports, familyName),
			OKButton=None,
		)
		print("❌ No active instances in Font Info. Aborting.")
	elif not exportPath:
		Message(
			title="⚠️ Specimenizer Error",
			message="Could not determine the export path. Export webfonts first, then run the script again.",
			OKButton=None,
		)
		print("❌ Could not determine export path. Aborting.")
	else:
		instanceInfoList = instanceInfos( thisFont, instances, fileFormat )
		for fileName, cssName, styleName in instanceInfoList:
			print("  ☑️ %s → %s" % (styleName, fileName))

		# variable font, if there is one:
		variableSection = ""
		firstVariableFontName = instanceInfoList[0][1]
		fontFacesCSS = fontFaces( instanceInfoList )
		vfInstances = variableInstances( thisFont, thisProject )
		axisInfos = axisInfosOfFont( thisFont )
		if vfInstances and axisInfos:
			vfFileFormat = "woff2" if fileFormat in ("woff2", "woff") else "ttf"
			vfInfoList = instanceInfos( thisFont, vfInstances[:1], vfFileFormat )
			firstVariableFontName = vfInfoList[0][1]
			fontFacesCSS += fontFaces( vfInfoList, isVariable=True, axisInfos=axisInfos )
			variableSection = variableSectionContent.replace( "{{axisSliders}}", axisSliders(axisInfos) )
			print("  🔠 Variable font: %s (%s)" % (vfInfoList[0][0], ", ".join([a[0] for a in axisInfos])))
		elif vfInstances:
			print("  ⚠️ Variable font export found, but could not determine axis ranges. Skipping axis sliders.")

		charSetCode, glyphCount = characterSet( thisFont )
		features = exportingFeatures( thisFont )
		print("  🔠 %i glyphs, %i features" % (glyphCount, len(features)))

		coverMeta = ""
		for label, value in (
			("", thisFont.designer),
			("", thisFont.manufacturer),
			("Version ", "%i.%03i" % (thisFont.versionMajor, thisFont.versionMinor)),
		):
			if value:
				coverMeta += "\t\t\t<span>%s%s</span>\n" % ( escapeHTML(label), escapeHTML(value) )

		replacements = (
			( "{{fontFaces}}\n", fontFacesCSS ),
			( "{{optionList}}\n", optionList(instanceInfoList) ),
			( "{{featureToggles}}\n", featureToggles(features) ),
			( "{{styleSections}}\n", styleSections(instanceInfoList) ),
			( "{{waterfallLines}}\n", waterfallLines() ),
			( "{{paragraphColumns}}\n", paragraphColumns() ),
			( "{{characterSet}}\n", charSetCode ),
			( "{{featureComparisons}}\n", featureComparisons(features) ),
			( "{{variableSection}}\n", variableSection ),
			( "{{coverMeta}}\n", coverMeta ),
			( "{{familyName}}", escapeHTML(familyName) ),
			( "{{firstFontName}}", escapeHTML(instanceInfoList[0][1]) ),
			( "{{firstVariableFontName}}", escapeHTML(firstVariableFontName) ),
			( "{{styleCount}}", str(len(instanceInfoList)) ),
			( "{{glyphCount}}", str(glyphCount) ),
			( "{{sampleLine}}", escapeHTML(defaultSampleLine) ),
			( "{{sampleParagraph}}", escapeJS(defaultParagraph) ),
			( "{{copyright}}", escapeHTML(thisFont.copyright) ),
			( "{{date}}", datetime.date.today().strftime("%Y-%m-%d") ),
		)
		specimenHTML = replaceSet( htmlContent, replacements )

		htmlFileName = "%s specimen.html" % familyName.replace("/", "-")
		if saveFileInLocation( content=specimenHTML, fileName=htmlFileName, filePath=exportPath ):
			print("✅ Done.")
			system( 'cd "%s"; open .; open "%s"' % (exportPath, htmlFileName) )
			Glyphs.showNotification(
				"%s: specimen created" % familyName,
				"%i styles, %i glyphs. Details in Macro Window." % (len(instanceInfoList), glyphCount),
			)
		else:
			print("❌ Error writing file to disk.")
