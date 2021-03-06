import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

from time import strftime

import pip

try:
  import girder_client
except ImportError:
  pip.main(['install', 'girder-client'])

#
# GirderStorageTest
#

class GirderStorageTest(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "GirderStorageTest" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# GirderStorageTestWidget
#

class GirderStorageTestWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    self.userEdit = qt.QLineEdit()
    parametersFormLayout.addRow("Girder user: ", self.userEdit)

    self.apiKeyEdit = qt.QLineEdit()
    parametersFormLayout.addRow("Girder API key: ", self.apiKeyEdit)

    self.apiUrl = qt.QLineEdit()
    parametersFormLayout.addRow("API URL: ", self.apiUrl)

    self.saveButton = qt.QPushButton("Save and upload to Girder")
    parametersFormLayout.addRow(self.saveButton)

    self.saveButton.connect('clicked(bool)', self.onSaveButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    settings = slicer.app.userSettings()
    username = settings.value(self.moduleName + '/' + self.moduleName + 'Username')
    api_key = settings.value(self.moduleName + '/' + self.moduleName + 'ApiKey')
    api_url = settings.value(self.moduleName + '/' + self.moduleName + 'ApiUrl')

    self.userEdit.setText(username)
    self.apiKeyEdit.setText(api_key)
    self.apiUrl.setText(api_url)


  def cleanup(self):
    pass

  def onSaveButton(self):
    logic =GirderStorageTestLogic()
    username = self.userEdit.text
    api_key = self.apiKeyEdit.text
    api_url = self.apiUrl.text

    settings = slicer.app.userSettings()
    settings.beginGroup(self.moduleName)
    settings.setValue(self.moduleName + 'Username', username)
    settings.setValue(self.moduleName + 'ApiKey', api_key)
    settings.setValue(self.moduleName + 'ApiUrl', api_url)
    settings.endGroup()

    logic.saveAndUploadScene(username, api_key, api_url)

#
# GirderStorageTestLogic
#

class GirderStorageTestLogic(ScriptedLoadableModuleLogic):

  def saveAndUploadScene(self, username, api_key, api_url):

    sceneName = "Scene-" + strftime("%Y%m%d-%H%M%S") + ".mrb"
    from os.path import expanduser
    home = expanduser("~")
    sceneSaveFilename = os.path.join(home, sceneName)

    print 'saving scene to file: ' + sceneSaveFilename

    slicer.util.saveScene(sceneSaveFilename)
    print 'saving file done'

    print 'saving to Girder'

    patient_folder = '5a54e3b6210e501a6c95f73b'
    import girder_client
    gc = girder_client.GirderClient(apiUrl=api_url)
    gc.authenticate(username=username, apiKey=api_key)

    # create an item
    item = gc.createItem(parentFolderId=patient_folder, name=sceneName)
    # set some metadata on the item
    metadata = {
      'patient_id': '0',
      'acquisition_date': '2018-01-12'
    }
    gc.addMetadataToItem(item['_id'], metadata)
    # upload the file itself
    # 'example.zip' is a local file
    gc.uploadFileToItem(itemId=item['_id'], filepath=sceneSaveFilename)


  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qimage = ctk.ctkWidgetsUtils.grabWidget(widget)
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('GirderStorageTestTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True


class GirderStorageTestTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_GirderStorageTest1()

  def test_GirderStorageTest1(self):

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = GirderStorageTestLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )

    # Girder test data
    username = 'girder'
    api_key = '' # Todo: add your API key created on the Girder server
    api_url = 'http://ec2-52-202-191-211.compute-1.amazonaws.com/api/v1'
    # logic.saveAndUploadScene(username, api_key, api_url)

    self.delayDisplay('Test passed!')
