#MenuTitle: Parameters Creator
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__="""
Creates custom parameters in Font Info > Font, Masters, Styles, in one or all open fonts. Write one ‘parameter = value’ per line to add several at once. Counterpart to Remove Custom Parameters.
"""

from GlyphsApp import *
from AppKit import NSFont
import vanilla

# frequently used parameters, shown in the menu together with the ones already in the font:
commonParameters = (
	"Axis Location",
	"Disable Subroutines",
	"Don't use Production Names",
	"Export Glyphs",
	"Family Alignment Zones",
	"Filter",
	"fsType",
	"glyphOrder",
	"hheaAscender",
	"hheaDescender",
	"hheaLineGap",
	"Keep Overlapping Components",
	"License",
	"License URL",
	"Name Table Entry",
	"panose",
	"postscriptBlueScale",
	"Preferred Family Name",
	"Preferred Subfamily Name",
	"Remove Glyphs",
	"Rename Glyphs",
	"Save as TrueType",
	"typoAscender",
	"typoDescender",
	"typoLineGap",
	"underlinePosition",
	"underlineThickness",
	"unitsPerEm",
	"Use Typo Metrics",
	"Variable Font Family Name",
	"Variable Font Origin",
	"weightClass",
	"widthClass",
	"winAscent",
	"winDescent",
)

def parsedValue( valueString ):
	"""Turns the typed value into a bool, int, float or string. Quotes force a string."""
	valueString = valueString.strip()
	if len(valueString) > 1 and valueString[0] == valueString[-1] and valueString[0] in ('"', "'", "“", "‘"):
		return valueString[1:-1]
	if valueString.startswith("“") and valueString.endswith("”"):
		return valueString[1:-1]
	lowercaseValue = valueString.lower()
	if lowercaseValue in ("yes", "true", "on"):
		return True
	if lowercaseValue in ("no", "false", "off"):
		return False
	try:
		return int(valueString)
	except:
		pass
	try:
		return float(valueString)
	except:
		pass
	return valueString

def parsedLines( text ):
	"""Turns the text of the entry field into a tuple of (name, value) tuples."""
	parameters = []
	for thisLine in text.splitlines():
		thisLine = thisLine.strip()
		if not thisLine or thisLine.startswith("#"):
			continue
		if "=" in thisLine:
			name, value = thisLine.split("=", 1)
			name = name.strip()
			if name:
				parameters.append( (name, parsedValue(value)) )
		else:
			# a parameter without a value is meant as a switch:
			parameters.append( (thisLine, True) )
	return tuple(parameters)

class ParametersCreator( object ):
	prefID = "com.rsztype.ParametersCreator"

	def __init__( self ):
		# Window 'self.w':
		windowWidth  = 350
		windowHeight = 260
		windowWidthResize  = 500 # user can resize width by this value
		windowHeightResize = 300 # user can resize height by this value
		self.w = vanilla.FloatingWindow(
			( windowWidth, windowHeight ), # default window size
			"Parameters Creator", # window title
			minSize = ( windowWidth, windowHeight ), # minimum size (for resizing)
			maxSize = ( windowWidth + windowWidthResize, windowHeight + windowHeightResize ), # maximum size (for resizing)
			autosaveName = "%s.mainwindow" % self.prefID # stores last window position and size
		)

		# UI elements:
		linePos, inset, lineHeight = 12, 15, 22

		self.w.descriptionText = vanilla.TextBox( (inset, linePos+2, -inset, 14), "Add one ‘parameter = value’ per line:", sizeStyle='small', selectable=True )
		linePos += lineHeight

		self.w.parameterEntry = vanilla.TextEditor( (inset, linePos, -inset, -120), "", callback=self.SavePreferences, checksSpelling=False )
		self.w.parameterEntry.getNSTextView().setToolTip_(
			"One parameter per line, e.g.:\n"
			"Use Typo Metrics = yes\n"
			"typoAscender = 800\n"
			"License URL = https://example.com\n\n"
			"Values are turned into numbers or yes/no switches where possible; put a value in quotes to keep it a string. "
			"A line without ‘=’ is added as a switched-on parameter. Lines starting with # are ignored."
		)
		self.w.parameterEntry.getNSTextView().setFont_( NSFont.userFixedPitchFontOfSize_(11) )

		self.w.parameterMenu = vanilla.PopUpButton( (inset, -110, -inset-70, 17), self.availableParameters(), sizeStyle='small' )
		self.w.parameterMenu.getNSPopUpButton().setToolTip_("Frequently used parameters, plus the ones already present in the open fonts.")
		self.w.insertButton = vanilla.SquareButton( (-inset-65, -111, -inset-22, 18), "Insert", sizeStyle='small', callback=self.insertParameter )
		self.w.insertButton.getNSButton().setToolTip_("Adds the parameter chosen on the left as a new line in the text field above.")
		self.w.updateButton = vanilla.SquareButton( (-inset-20, -111, -inset, 18), "↺", sizeStyle='small', callback=self.updateMenu )
		self.w.updateButton.getNSButton().setToolTip_("Rescans the open fonts and updates the menu to the left.")

		self.w.addToText = vanilla.TextBox( (inset, -85, 100, 14), "To Font Info >", sizeStyle='small', selectable=True )
		self.w.addToFont = vanilla.CheckBox( (inset+95+50*0, -88, 60, 20), "Font", value=True, callback=self.SavePreferences, sizeStyle='small' )
		self.w.addToFont.getNSButton().setToolTip_("If enabled, will add the parameters to File > Font Info > Font.")
		self.w.addToMasters = vanilla.CheckBox( (inset+95+50, -88, 70, 20), "Masters", value=False, callback=self.SavePreferences, sizeStyle='small' )
		self.w.addToMasters.getNSButton().setToolTip_("If enabled, will add the parameters to all masters in File > Font Info > Masters.")
		self.w.addToStyles = vanilla.CheckBox( (inset+95+120, -88, -inset, 20), "Styles" if Glyphs.versionNumber >= 3.0 else "Instances", value=False, callback=self.SavePreferences, sizeStyle='small' )
		self.w.addToStyles.getNSButton().setToolTip_("If enabled, will add the parameters to the styles in File > Font Info > Styles (Instances in Glyphs 2).")

		self.w.exportingOnly = vanilla.CheckBox( (inset, -66, 150, 20), "Exporting styles only", value=True, callback=self.SavePreferences, sizeStyle='small' )
		self.w.exportingOnly.getNSButton().setToolTip_("If enabled, will skip styles that are set to not export.")
		self.w.overwrite = vanilla.CheckBox( (inset+160, -66, -inset, 20), "Overwrite existing", value=True, callback=self.SavePreferences, sizeStyle='small' )
		self.w.overwrite.getNSButton().setToolTip_("If enabled, resets parameters that are already there. If disabled, existing parameters keep their values.")

		self.w.addInText = vanilla.TextBox( (inset, -43, 62, 14), "Add in", sizeStyle='small', selectable=True )
		self.w.addIn = vanilla.PopUpButton( (inset+62, -45, 150, 17), ("current font", "⚠️ ALL open fonts"), sizeStyle='small', callback=self.SavePreferences )
		self.w.addIn.getNSPopUpButton().setToolTip_("Choose here in which font you want to create the parameters. Careful with the ‘All open fonts’ choice.")

		# Run Button:
		self.w.runButton = vanilla.Button( (-80-inset, -20-inset, -inset, -inset), "Create", sizeStyle='regular', callback=self.ParametersCreatorMain )
		self.w.setDefaultButton( self.w.runButton )

		# Load Settings:
		if not self.LoadPreferences():
			print("Note: 'Parameters Creator' could not load preferences. Will resort to defaults")

		# Open window and focus on it:
		self.updateUI()
		self.w.open()
		self.w.makeKey()

	def domain( self, prefName ):
		return "%s.%s" % (self.prefID, prefName.strip())

	def pref( self, prefName ):
		return Glyphs.defaults[ self.domain(prefName) ]

	def availableParameters( self, sender=None ):
		parameterNames = set(commonParameters)
		for thisFont in Glyphs.fonts:
			for parameter in thisFont.customParameters:
				parameterNames.add( parameter.name )
			for master in thisFont.masters:
				for parameter in master.customParameters:
					parameterNames.add( parameter.name )
			for instance in thisFont.instances:
				for parameter in instance.customParameters:
					parameterNames.add( parameter.name )
		return sorted( parameterNames, key=lambda parameterName: parameterName.lower() )

	def updateMenu( self, sender=None ):
		self.w.parameterMenu.setItems( self.availableParameters() )

	def insertParameter( self, sender=None ):
		parameterName = self.w.parameterMenu.getItem()
		if not parameterName:
			return
		text = self.w.parameterEntry.get()
		if text and not text.endswith("\n"):
			text += "\n"
		self.w.parameterEntry.set( "%s%s = " % (text, parameterName) )
		self.SavePreferences()

	def updateUI( self, sender=None ):
		hasParameters = bool( parsedLines( self.w.parameterEntry.get() ) )
		hasTarget = self.w.addToFont.get() or self.w.addToMasters.get() or self.w.addToStyles.get()
		self.w.exportingOnly.enable( self.w.addToStyles.get() )
		self.w.runButton.enable( hasParameters and hasTarget )

	def SavePreferences( self, sender=None ):
		try:
			# write current settings into prefs:
			Glyphs.defaults[ self.domain("parameterEntry") ] = self.w.parameterEntry.get()
			Glyphs.defaults[ self.domain("addToFont") ] = self.w.addToFont.get()
			Glyphs.defaults[ self.domain("addToMasters") ] = self.w.addToMasters.get()
			Glyphs.defaults[ self.domain("addToStyles") ] = self.w.addToStyles.get()
			Glyphs.defaults[ self.domain("exportingOnly") ] = self.w.exportingOnly.get()
			Glyphs.defaults[ self.domain("overwrite") ] = self.w.overwrite.get()
			Glyphs.defaults[ self.domain("addIn") ] = self.w.addIn.get()

			if sender == self.w.addIn:
				self.updateMenu()

			self.updateUI()
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	def LoadPreferences( self ):
		try:
			# register defaults:
			Glyphs.registerDefault( self.domain("parameterEntry"), "" )
			Glyphs.registerDefault( self.domain("addToFont"), 1 )
			Glyphs.registerDefault( self.domain("addToMasters"), 0 )
			Glyphs.registerDefault( self.domain("addToStyles"), 0 )
			Glyphs.registerDefault( self.domain("exportingOnly"), 1 )
			Glyphs.registerDefault( self.domain("overwrite"), 1 )
			Glyphs.registerDefault( self.domain("addIn"), 0 )

			# load previously written prefs:
			self.w.parameterEntry.set( self.pref("parameterEntry") )
			self.w.addToFont.set( self.pref("addToFont") )
			self.w.addToMasters.set( self.pref("addToMasters") )
			self.w.addToStyles.set( self.pref("addToStyles") )
			self.w.exportingOnly.set( self.pref("exportingOnly") )
			self.w.overwrite.set( self.pref("overwrite") )
			self.w.addIn.set( self.pref("addIn") )

			self.updateUI()
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	def currentFonts( self, sender=None ):
		goThroughAllOpenFonts = self.pref("addIn")
		if goThroughAllOpenFonts:
			return Glyphs.fonts
		else:
			return (Glyphs.font,) # frontmost font only

	def setParameter( self, thisObject, parameterName, parameterValue, overwrite, objectDescription ):
		"""Sets one parameter on font, master or instance. Returns 1 if it was written, 0 if it was skipped."""
		existingValue = thisObject.customParameters[parameterName]
		if existingValue is not None and not overwrite:
			print("  ⚠️ %s: kept existing ‘%s’ = %s" % (objectDescription, parameterName, existingValue))
			return 0
		thisObject.customParameters[parameterName] = parameterValue
		if existingValue is None:
			print("  ✅ %s: added ‘%s’ = %s" % (objectDescription, parameterName, parameterValue))
		else:
			print("  ♻️ %s: reset ‘%s’ = %s (was: %s)" % (objectDescription, parameterName, parameterValue, existingValue))
		return 1

	def ParametersCreatorMain( self, sender=None ):
		try:
			# clear macro window log:
			Glyphs.clearLog()

			# update settings to the latest user input:
			if not self.SavePreferences():
				print("Note: 'Parameters Creator' could not write preferences.")

			if len(Glyphs.fonts) == 0:
				Message( title="No Font Open", message="The script requires a font. Open a font and run the script again.", OKButton=None )
				return

			parameters = parsedLines( self.pref("parameterEntry") )
			if not parameters:
				Message( title="No Parameters", message="Write at least one ‘parameter = value’ line, then run the script again.", OKButton=None )
				return

			addToFont = self.pref("addToFont")
			addToMasters = self.pref("addToMasters")
			addToStyles = self.pref("addToStyles")
			exportingOnly = self.pref("exportingOnly")
			overwrite = self.pref("overwrite")

			theseFonts = self.currentFonts()
			writtenParameterCount = 0

			for thisFont in theseFonts:
				print("Parameters Creator Report for %s" % thisFont.familyName)
				if thisFont.filepath:
					print(thisFont.filepath)
				else:
					print("⚠️ The font file has not been saved yet.")
				print()

				for parameterName, parameterValue in parameters:
					if addToFont:
						writtenParameterCount += self.setParameter( thisFont, parameterName, parameterValue, overwrite, "Font" )

					if addToMasters:
						for thisMaster in thisFont.masters:
							writtenParameterCount += self.setParameter( thisMaster, parameterName, parameterValue, overwrite, "Master %s" % thisMaster.name )

					if addToStyles:
						for thisInstance in thisFont.instances:
							if exportingOnly and not thisInstance.active:
								continue
							writtenParameterCount += self.setParameter( thisInstance, parameterName, parameterValue, overwrite, "Style %s" % thisInstance.name )
				print()

			self.w.close() # delete if you want window to stay open

			# Final report:
			Glyphs.showNotification(
				"Created Parameters in %i Font%s" % (
					len(theseFonts),
					"" if len(theseFonts)==1 else "s",
				),
				"Wrote %i parameter%s. Details in Macro Window." % (
					writtenParameterCount,
					"" if writtenParameterCount==1 else "s",
				),
			)
			print("Done.")

		except Exception as e:
			# brings macro window to front and reports error:
			Glyphs.showMacroWindow()
			print("Parameters Creator Error: %s" % e)
			import traceback
			print(traceback.format_exc())

ParametersCreator()
