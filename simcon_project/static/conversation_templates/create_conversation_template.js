// Character count max values from models
let CHOICE_DESCRIPTION_CHAR_MAX = 500
let TEMPLATE_NAME_CHAR_MAX = 100
let TEMPLATE_DESCRIPTION_CHAR_MAX = 4000
let TEMPLATE_NODE_DESCRIPTION_CHAR_MAX = 4000
let EXAMPLE_CONVERSATION_CHAR_MAX = 4000

// Error message(s) used in multiple places
let NO_DESTINATION_FOR_CHOICE_ERROR = "No destination selected"

// Variables used to keep track of state that will eventually get sent to the backend
let templateName = ""           // Holds template's name
let templateDescription = ""    // Holds template's description
let exampleConversation = ""    // Holds example conversation that a user can provide
let nodes = new Map()           // Map from counter to node. Used to keep track of all the created nodes
let formSubmitted = false       // Used to indicate if a form was submitted successfully

// Variables used purely for client side purposes
let validating = false          // Indicates if validation is turned on or not
let lastUsedNodeIndex = 0       // Counter to be iterated and used as key in nodes map when a new node is created
let currentNodeInFocus = null   // Used to keep track of what node is currently being worked on

// Holds all the information about a single step node
class StepNode {
    constructor() {
        // Items used only for manipulations on the client side
        this.index = 0                      // Used to keep track of node's index in the nodes map (redundant but convenient)
        this.nodeName = ""                  // Node's name
        this.lastChoiceIndex = 0            // Used to keep track of the last choice index used (used as key in responseChoices map below)

        // Items to be propagated to the backend
        this.responseChoices = new Map()    // Array of choices for this node
        this.videoUrl = ""                  // Stores non-embeddable video url (url as user provides it)
        this.nodeDescription = ""           // Node's description
        this.isFirst = false                // True if node is first
        this.isTerminal = false             // True if node is terminal
    }

    // Used when submitting to the backend (when JSON.stringify() is called)
    toJSON() {
        return {
            videoURL: this.videoUrl,
            description: this.nodeDescription,
            isFirst: this.isFirst,
            isTerminal: this.isTerminal,
            responseChoices: Array.from(this.responseChoices.values())
        }
    }
}

// Used inside StepNode to hold available choices at that step
class Choice {
    constructor(description, destinationIndex) {
        this.description = description
        this.destinationIndex = destinationIndex // Stores the node index that serves as the destination for this choice
        // (associated with the 'value' element inside the relevant 'option' in a destination 'select' [look at choice cards])
        // 0 if no destination selected
    }
}

/**
 * Submits constructed nodes objects to the backend
 */
function submit() {
    // Checks that everything is valid before submission
    let everythingIsValid = true
    let foundFirst = false
    if(validateTemplateNameInput() && validateTemplateDescriptionInput() && validateExampleConversationInput()){
        nodes.forEach((node) => {
            if(!nodeIsValid(node)){
                everythingIsValid = false
            }
            if(node.isFirst) {
                foundFirst = true
            }
        })
    } else {
        everythingIsValid = false
    }

    if(everythingIsValid && foundFirst) {
        // Retrieves csrftoken
        let csrftoken = null
        const cookieName = "csrftoken"
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";")
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim()
                if (cookie.substring(0, cookieName.length + 1) === (cookieName + "=")) {
                    csrftoken = decodeURIComponent(cookie.substring(cookieName.length + 1))
                    break
                }
            }
        }

        const postBody = JSON.stringify({
            nodes: Array.from(nodes),
            templateName: templateName,
            templateDescription: templateDescription,
            exampleConversation: exampleConversation
        })

        // Determines the post url without direct hard coding.
        let currentUrl = window.location.href
        let postUrl = ""
        if(modelObject) {
            postUrl = currentUrl.split("edit")[0] + "new/"
        } else {
            postUrl = currentUrl
        }

        // Make POST request
        fetch(postUrl, {
            method: "POST",
            credentials: "include",
            mode: "same-origin",
            body: postBody,
            headers: new Headers({
                "X-CSRFToken": csrftoken,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest"
            })
        }).then(function(response) {
            if(response.ok) {
                formSubmitted = true
                alert("Template saved successfully")
                if(modelObject) {
                    window.location.replace(window.location.href.split('edit')[0])
                } else {
                    window.location.replace(window.location.href.split('new')[0])
                }
            } else throw new Error(response.status)
        }).catch(function (error) {
            alert("Something went wrong while submitting the form\n" + error)
        })
    } else { // If the input was invalid turn on validation and validate everything
        validating = true
        getValidateToggle().checked = true
        alert("There are issues with the template")
        updateValidityIndicatorOnAllStepNodes()
        validateAllVisibleFields()
        validateIsFirstNodeCheck()
    }
}

/**
 * Called on page load. Sets the listeners and initializes page content.
 */
function loadState() {
    $(document).ready(() => {

        if(modelObject) {
            modelObject.nodes.reverse() //Reverse the order of the template nodes so they are rendered in the same order as they did when the template was created
            templateDescription = modelObject.description
            templateName = modelObject.name
            exampleConversation = modelObject.example_conversation

            let nodeIdToIndexMap = new Map()
            for(const serverNode of modelObject.nodes) {
                nodeIdToIndexMap.set(serverNode.id, lastUsedNodeIndex + 1)
                addStepNode()
            }
            for(const serverNode of modelObject.nodes) {
                let clientNode = nodes.get(nodeIdToIndexMap.get(serverNode.id))

                for(const serverChoiceNode of serverNode.choices) {
                    let serverChoiceNodeDestination = nodeIdToIndexMap.get(serverChoiceNode.choice_destination)
                    if(serverChoiceNodeDestination == "" || !serverChoiceNodeDestination) {
                       serverChoiceNodeDestination = 0
                    } else {
                        serverChoiceNodeDestination = Number(serverChoiceNodeDestination)
                    }
                    clientNode.responseChoices.set(clientNode.lastChoiceIndex, new Choice(
                        serverChoiceNode.choice_text,
                        serverChoiceNodeDestination
                    ))
                    clientNode.lastChoiceIndex++
                }
                clientNode.videoUrl = serverNode.video_url
                clientNode.nodeDescription = serverNode.description
                clientNode.isFirst = serverNode.start
                clientNode.isTerminal = serverNode.terminal
            }

            updateNodeInFocus(1)
            getTemplateNameInput().value = templateName
            getTemplateDescriptionInput().value = templateDescription
            getExampleConversationInput().value = exampleConversation
        } else {
            addStepNode()
            updateNodeInFocus(1)
            currentNodeInFocus.isFirst = true
            getFirstStepToggle().checked = true
        }

        // Enable tooltips (bootstrap)
        $("[data-toggle='tooltip']").tooltip()

        // Warn on page reload and leave.
        window.onbeforeunload =  function (e) {
            if(!formSubmitted) {
                let confirmationMessage = "Leaving or reloading the page will result in all progress being lost";

                (e || window.event).returnValue = confirmationMessage
                return confirmationMessage
            }
        }

        // When an input is changed, properly handle that input
        $(document).on("input", "input, textarea, select", function (event) {
            let element = event.target
            let elementID = element.id

            switch (elementID) {
                case "video-url-input":
                    handleURLInput()
                    break
                case "node-name-input":
                    handleNodeNameInput()
                    break
                case "node-description-input":
                    handleNodeDescriptionInput()
                    break
                case "is-first-node-check":
                    handleIsFirstNodeCheck()
                    break
                case "is-terminal-node-check":
                    handleIsTerminalNodeCheck()
                    break
                case "template-name-input":
                    handleTemplateNameInput()
                    break
                case "template-description-input":
                    handleTemplateDescriptionInput()
                    break
                case "template-example-conversation-input":
                    handleExampleConversationInput()
                    break
                case "validate-check-input":
                    handleValidateToggle()
                    break
                default:    // Can't match ids of choice card inputs since they are indexed ie. choiceDescriptionInput-0
                    if(elementID.split("-")[0] == "choiceDescriptionInput") {
                        handleChoiceDescriptionInput(Number(elementID.split("-")[1]))
                    } else {
                        handleChoiceDestinationSelect(Number(elementID.split("-")[1]))
                    }
            }

            if(validating) updateNodeValidityIndicator(currentNodeInFocus)
        })

        // When a step node card is clicked, that card's context has to be focused
        $(document).on("click", ".step-node-card", function () {
            let clickedNodeId = parseInt($(this).attr("id").split("-")[1])
            if(!(nodes.get(clickedNodeId) === currentNodeInFocus)) updateNodeInFocus(clickedNodeId)
        })

        // Every step node card has a 'Delete' link
        // If click propagation is not stopped, the parent card's onclick event defined above is also triggered when Delete is clicked
        $(document).on("click", ".remove-step-node", function (event) {
            event.stopPropagation()
        })

        // When user updates the video url, updates the embedded video
        $("#video-url-input").blur(() => {
            setEmbeddedVideoUrl(getVideoUrlInput().value.trim())
        })
    })
}

/**
 * Given a node index, switches focus to it by updating the input and choice data.
 *
 * @param nodeIndex index of the node to be put in focus
 */
function updateNodeInFocus(nodeIndex) {
    // Highlight currently selected node and make all others unhighlighted
    if(currentNodeInFocus !== null) $("#step-"+currentNodeInFocus.index).css("background-color", "white")
    $("#step-"+nodeIndex).css("background-color", " \t#aeb3b5")

    currentNodeInFocus = nodes.get(nodeIndex)

    // Update choice cards
    document.querySelectorAll(".choice-card").forEach(e => e.remove())
    let currentNodeResponseChoices = currentNodeInFocus.responseChoices
    currentNodeResponseChoices.forEach((value, key) => {
        addChoice(key, value.description, value.destinationIndex)
    })

    // Update the various input/toggle fields
    getNodeNameInput().value = currentNodeInFocus.nodeName
    getNodeDescriptionInput().value = currentNodeInFocus.nodeDescription
    getFirstStepToggle().checked = currentNodeInFocus.isFirst
    getTerminalStepToggle().checked = currentNodeInFocus.isTerminal
    getVideoUrlInput().value = currentNodeInFocus.videoUrl
    setEmbeddedVideoUrl(currentNodeInFocus.videoUrl)

    if(validating) validateAllVisibleFields()
}

/**
 * Adds a step node card to the step node card column and adds a step node to the nodes map
 */
function addStepNode() {
    lastUsedNodeIndex++

    let nodeToAdd = new StepNode()
    nodeToAdd.index = lastUsedNodeIndex
    nodeToAdd.nodeName = String(lastUsedNodeIndex)
    nodes.set(lastUsedNodeIndex, nodeToAdd)

    let newSelectOption = `<option value ="${lastUsedNodeIndex}">${lastUsedNodeIndex}</option>`
    $(".custom-select").append(newSelectOption)

    let stepNodeCard = `
        <div class="card mb-3 step-node-card" id="step-${lastUsedNodeIndex}">
            <div class="card-body">
                <h6 class="card-title">${lastUsedNodeIndex}</h6>
                <h6 class="card-subtitle mb-2 text-muted invalid-indicator" id="invalid-indicator-${lastUsedNodeIndex}">*</h6>
                <a href="javascript:removeStepNode(${lastUsedNodeIndex})" class="card-link remove-step-node">Delete</a>
            </div>
        </div>
    `
    $("#nodes-column .column-button-container:first-child").after(stepNodeCard)

    if(validating) updateNodeValidityIndicator(nodes.get(lastUsedNodeIndex))
}

/**
 * Removes a step node
 * This involves:
 *      -removing the appropriate card from the step node card column
 *      -updating the choices for all nodes stored in the 'nodes' map to not point to the removed node if they do
 *      -if removed node is in focus changing focus to another card
 *      -if removed node is not in focus, updating currently visible destination selects to not list removed node as an
 *          option and to be unselected if removed node is selected
 *
 * @param nodeIndex
 */
function removeStepNode(nodeIndex) {
    // Delete the relevant step node card
    let card = document.getElementById("step-" + nodeIndex)
    card.parentElement.removeChild(card)
    nodes.delete(nodeIndex)

    // Update the choices of stored steps to point to 0 if they point to removed step
    nodes.forEach((stepValue) => {
        let choicesOriginal = stepValue.responseChoices
        let choicesCopy = new Map(choicesOriginal)
        choicesCopy.forEach((choiceValue, choiceIndex) => {
            if(choiceValue.destinationIndex == nodeIndex) {
                choicesOriginal.set(choiceIndex, new Choice(choiceValue.description, 0))
            }
        })
    })

    // If removing a node that is not in focus (so step cards will not be rerendered), update selects
    if(nodeIndex != currentNodeInFocus.index) {
        let selects = document.getElementsByTagName("select")
        for(const select of selects) {
            if(select.value == nodeIndex) {
                select.value = 0
                if(validating) {
                    setElementAsInvalid(select, NO_DESTINATION_FOR_CHOICE_ERROR)
                }
            }
            select.removeChild(select.querySelector("[value='" + nodeIndex +"']"))
        }
    } else { // If removing the node that's currently in focus
        if(nodes.size == 0) { // If removing last standing step node
            lastUsedNodeIndex = 0
            addStepNode()
            updateNodeInFocus(1)
            currentNodeInFocus.isFirst = true
            getFirstStepToggle().checked = true
        } else { // If there are nodes left to which we can switch focus
            updateNodeInFocus(Array.from(nodes.keys()).reduce((lastKey, currKey) => nodes.get(currKey) !== undefined ? currKey : lastKey))
        }
    }
    if(validating) validateIsFirstNodeCheck()
}

/**
 * Used to generate possible destination options when creating choice cards
 * Marks one choice as 'selected' if 'selectedValue' parameter is not 0
 *
 * @param selectedValue index of the selected destination (0 if none selected)
 * @returns {string} HTML literal with the options to be inserted inside an 'insert' element
 */
function generateSelectOptions(selectedValue = 0) {
    let literalToReturn

    if(selectedValue == 0) { // If no destination was selected for this select element, make the select description choice 'selected'
        literalToReturn = `<option disabled selected value="0"> -- select destination -- </option>`
    } else {
        literalToReturn = `<option disabled value="0"> -- select destination -- </option>`
    }

    if(!currentNodeInFocus.isTerminal) {
        nodes.forEach((value, key) => {
            if(value !== currentNodeInFocus) {
                if(selectedValue == key) {
                    literalToReturn += `<option selected value="${key}">${nodes.get(key).nodeName}</option>`
                } else {
                    literalToReturn += `<option value="${key}">${nodes.get(key).nodeName}</option>`
                }
            }
        })
    }
    return literalToReturn
}

/**
 * Adds a choice card to the choice column
 * If creating a new choice, also adds the choice to the choice map inside current node
 *
 * @param choiceIndex specifies the index of the choice to be added. -1 if adding a new choice
 * @param choiceDescription description of the node
 * @param selectedValue index of the node's destination. O if creating a new node... 0 means unselected
 */
function addChoice(choiceIndex = -1, choiceDescription = "", selectedValue = 0) {
    if(choiceIndex == -1) { // Updates current node's choices map if this function was called to create a new choice
        choiceIndex = ++currentNodeInFocus.lastChoiceIndex
        currentNodeInFocus.responseChoices.set(choiceIndex, new Choice("", 0))
    }

    let htmlToAdd = `
        <div class="card mb-3 choice-card" id="choice-${choiceIndex}">
            <div class="card-body">
            
                <form novalidate>
                    <div class="form-group">
                        <label for="choiceDescriptionInput-${choiceIndex}">Choice description:</label>
                        <textarea class="form-control" id="choiceDescriptionInput-${choiceIndex}" data-toggle="tooltip" title="">${choiceDescription}</textarea>
                    </div>
                </form>
                
            <select class="custom-select" data-toggle="tooltip" title="" id="choiceDestinationSelect-${choiceIndex}">
            ${generateSelectOptions(selectedValue)}
            </select>
            <a href="javascript:removeChoice(${choiceIndex})" class="card-link">Delete</a>
            </div>
        </div>
        `
    $("#choices-column .column-button-container:first-child").after(htmlToAdd)

    if(validating) {
        document.getElementById("no-choices-error").style.display = "none"
        validateChoiceDestinationSelect(choiceIndex)
        validateChoiceDescriptionInput(choiceIndex)
    }
}

/**
 * Used to delete a choice (both from the choice card column and current node's choices map)
 * @param choiceIndex
 */
function removeChoice(choiceIndex) {
    let choiceCard = document.getElementById("choice-" + choiceIndex)
    choiceCard.parentElement.removeChild(choiceCard)
    currentNodeInFocus.responseChoices.delete(choiceIndex)

    if(validating) validateResponseChoices()
}

/**
 *
 * @param url YouTube url to embed. Does not have to match embeddable style
 * @returns {string}
 */
function getEmbeddableUrl(url) {
    const REGEX = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/
    const match = url.match(REGEX)
    const regexedUrl = (match&&match[7].length==11)? match[7] : ""
    if(!(regexedUrl == "")) {
        return "https://www.youtube-nocookie.com/embed/" + regexedUrl + "?rel=0&modestbranding=1&wmode=opaque"
    }
    return ""
}


/*********************************************************************************************************************/
/**
 * Input handlers
 */

function handleNodeNameInput() {
    const input = getNodeNameInput().value.trim()
    $("#step-" + currentNodeInFocus.index + " .card-title").text(input)
    currentNodeInFocus.nodeName = input
}

function handleURLInput() {
    currentNodeInFocus.videoUrl = getVideoUrlInput().value.trim()
    if(validating) validateURLInput()
}

function handleNodeDescriptionInput() {
    currentNodeInFocus.nodeDescription = getNodeDescriptionInput().value.trim()
    if(validating) validateNodeDescriptionInput()
}

function handleIsFirstNodeCheck() {
    const element = getFirstStepToggle()
    const checked = element.checked

    currentNodeInFocus.isFirst = checked

    // Go through and mark every other node as not first
    if(checked) {
        nodes.forEach((value) => {
            value.isFirst = value === currentNodeInFocus
        })
    }

    if(validating) validateIsFirstNodeCheck()
}

function handleIsTerminalNodeCheck() {
    const checked = getTerminalStepToggle().checked

    currentNodeInFocus.isTerminal = checked

    // Updates selects visible on the page
    const selects = document.getElementsByTagName("select")
    for(const select of selects) {
        select.innerHTML = generateSelectOptions()
    }

    // Resets destination for all current node's choices to 0 in memory
    if(checked) {
        currentNodeInFocus.responseChoices.forEach((choiceValue, choiceIndex) => { choiceValue.destinationIndex = 0 })
    }

    if(validating) validateResponseChoices()
}

function handleTemplateNameInput() {
    templateName = getTemplateNameInput().value.trim()
    if(validating) validateTemplateNameInput()
}

function handleTemplateDescriptionInput() {
    templateDescription = getTemplateDescriptionInput().value.trim()
    if(validating) validateTemplateDescriptionInput()
}

function handleExampleConversationInput() {
    exampleConversation = getExampleConversationInput().value.trim()
    if(validating) validateExampleConversationInput()
}

function handleChoiceDescriptionInput(choiceIndex) {
    currentNodeInFocus.responseChoices.get(choiceIndex).description = getChoiceDescriptionInput(choiceIndex).value.trim()
    if(validating) validateChoiceDescriptionInput(choiceIndex)
}

function handleChoiceDestinationSelect(choiceIndex) {
    currentNodeInFocus.responseChoices.get(choiceIndex).destinationIndex = Number(getChoiceDestinationSelect(choiceIndex).value)
    if(validating) validateChoiceDestinationSelect(choiceIndex)
}
/*********************************************************************************************************************/


/*********************************************************************************************************************/
/**
 * Validation functions
 */

/**
 * Called when validate toggle is toggled
 */
function handleValidateToggle() {
    const checked = getValidateToggle().checked
    if(checked == true) {
        validating = true
        validateAllVisibleFields()
        updateValidityIndicatorOnAllStepNodes()
    } else {
        validating = false
        setElementAsValid(getVideoUrlInput())
        setElementAsValid(getNodeDescriptionInput())
        setElementAsValid(getTemplateNameInput())
        setElementAsValid(getTemplateDescriptionInput())
        nodes.forEach((node) => {
            document.getElementById("invalid-indicator-" + node.index).style.display = "none"
        })
        document.getElementById("no-first-node-error").style.display = "none"
        document.getElementById("no-choices-error").style.display = "none"
        currentNodeInFocus.responseChoices.forEach((value, key) => {
            setElementAsValid(getChoiceDescriptionInput(key))
            setElementAsValid(getChoiceDestinationSelect(key))
        })
    }
}

function setElementAsInvalid(element, message) {
    element.setAttribute("title", message)
    element.classList.add("invalid")
}

function setElementAsValid(element) {
    element.setAttribute("title", "")
    element.classList.remove("invalid")
}

/**
 * Used to handle validity of a text input
 * @param element element who's validity is to be checked
 * @param charLimit max characters for this input
 * @returns {boolean} indicating if the field is valid (ture if yes, false otherwise)
 */
function validateRequiredTextField(element, input, charLimit) {
    if(input == "") {
        setElementAsInvalid(element, "Must be non-empty")
    } else if(input.length > charLimit) {
        setElementAsInvalid(element, "Must be no longer than " + charLimit + " characters")
    } else {
        setElementAsValid(element)
        return true
    }
}

/**
 *  Checks if a node's data is valid
 * @param node the node who's validity is to be checked
 * @returns {boolean}
 */
function nodeIsValid(node) {
    if(
        node.nodeDescription == "" ||
        node.nodeDescription.length > TEMPLATE_NODE_DESCRIPTION_CHAR_MAX ||
        node.videoUrl == "" ||
        getEmbeddableUrl(node.videoUrl) == "" ||
        node.responseChoices.size == 0
    ) {
        return false
    }

    if(node.responseChoices.size == 0) return false

    let choicesValid = true
    node.responseChoices.forEach((value) => {
        if(
            value.description == "" ||
            value.description.length > CHOICE_DESCRIPTION_CHAR_MAX ||
            ((!node.isTerminal) && value.destinationIndex == 0)
        )
        {
            choicesValid = false
        }
    })

    return choicesValid
}

/**
 * Updates the validity indicator of all visible fields
 */
function validateAllVisibleFields() {
    validateURLInput()
    validateNodeDescriptionInput()
    validateTemplateNameInput()
    validateTemplateDescriptionInput()
    validateExampleConversationInput()
    validateResponseChoices()
    validateIsFirstNodeCheck()
}

/**
 * Updates node validity indicator on a node (*)
 * @param node node who's validity indicator is to be updated
 */
function updateNodeValidityIndicator(node) {
    if(!nodeIsValid(node)) {
        document.getElementById("invalid-indicator-" + node.index).style.display = "block"
    }
    else {
        document.getElementById("invalid-indicator-" + node.index).style.display = "none"
    }
}

/**
 * Updates the validity indicator on all node cards
 */
function updateValidityIndicatorOnAllStepNodes() {
    nodes.forEach((value) => {
        updateNodeValidityIndicator(value)
    })
}

function validateURLInput() {
    const element = getVideoUrlInput()
    const input = element.value.trim()

    if(input == "") {
        setElementAsInvalid(element, "Must be non-empty")
    } else if(getEmbeddableUrl(input) == "") {
        setElementAsInvalid(element, "Not a valid YouTube url")
    } else {
        setElementAsValid(element)
    }
}

function validateNodeDescriptionInput() {
    const element = getNodeDescriptionInput()
    const input = element.value.trim()
    validateRequiredTextField(element, input, TEMPLATE_NODE_DESCRIPTION_CHAR_MAX)
}

function validateIsFirstNodeCheck() {
    let foundFirst = false
    nodes.forEach((value, key) => {
        if(value.isFirst) {
            foundFirst = true
        }
    })

    if(!foundFirst) {
        document.getElementById("no-first-node-error").style.display = "block"
    } else {
        document.getElementById("no-first-node-error").style.display = "none"
    }
}

function validateTemplateNameInput() {
    const element = getTemplateNameInput()
    const input = element.value.trim()
    return validateRequiredTextField(element, input, TEMPLATE_NAME_CHAR_MAX)
}

function validateTemplateDescriptionInput() {
    const element = getTemplateDescriptionInput()
    const input = element.value.trim()
    return validateRequiredTextField(element, input, TEMPLATE_DESCRIPTION_CHAR_MAX)
}

function validateExampleConversationInput() {
    const element = getExampleConversationInput()
    if(element.value.trim().length > EXAMPLE_CONVERSATION_CHAR_MAX) {
        setElementAsInvalid(element, "Must be no longer than " + EXAMPLE_CONVERSATION_CHAR_MAX + " characters")
        return false
    } else {
        setElementAsValid(element)
        return true
    }
}

function validateChoiceDescriptionInput(choiceIndex) {
    const element = getChoiceDescriptionInput(choiceIndex)
    const input = element.value.trim()
    validateRequiredTextField(element, input, CHOICE_DESCRIPTION_CHAR_MAX)
}

function validateChoiceDestinationSelect(choiceIndex) {
    const element = getChoiceDestinationSelect(choiceIndex)
    if(element.value == 0 && !currentNodeInFocus.isTerminal) {
        setElementAsInvalid(element, NO_DESTINATION_FOR_CHOICE_ERROR)
    } else {
        setElementAsValid(element)
    }
}

function validateResponseChoices() {
    if(currentNodeInFocus.responseChoices.size == 0) {
        document.getElementById("no-choices-error").style.display = "block"
    } else {
        document.getElementById("no-choices-error").style.display = "none"
    }
    for(const key of currentNodeInFocus.responseChoices.keys()) {
        validateChoiceDescriptionInput(key)
        validateChoiceDestinationSelect(key)
    }
}
/*********************************************************************************************************************/


/*********************************************************************************************************************/
/**
 * DOM getters and setters
 */

function getTemplateNameInput() {
    return document.getElementById("template-name-input")
}

function getTemplateDescriptionInput() {
    return document.getElementById("template-description-input")
}

function getExampleConversationInput() {
    return document.getElementById("template-example-conversation-input")
}

function getNodeNameInput() {
    return document.getElementById("node-name-input")
}

function getNodeDescriptionInput() {
    return document.getElementById("node-description-input")
}

function getFirstStepToggle() {
    return document.getElementById("is-first-node-check")
}

function getTerminalStepToggle() {
    return document.getElementById("is-terminal-node-check")
}

function getVideoUrlInput() {
    return document.getElementById("video-url-input")
}

function getChoiceDestinationSelect(choiceIndex) {
    return document.getElementById("choiceDestinationSelect-" + String(choiceIndex))
}

function getChoiceDescriptionInput(choiceIndex) {
    return document.getElementById("choiceDescriptionInput-" + String(choiceIndex))
}

function getValidateToggle() {
    return document.getElementById("validate-check-input")
}

function setEmbeddedVideoUrl(url) {
    document.getElementById("embedded-video-iframe").setAttribute("src", getEmbeddableUrl(url))
}
/*********************************************************************************************************************/
