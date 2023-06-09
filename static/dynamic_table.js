function addField(plusElement){
    if (rowNum === (maxRowNum + 1)) {
        return false;
    }

    let lastField = document.getElementById("fieldTable").lastChild;

//    let secondField = plusElement.previousElementSibling
//    let firstField = secondField.previousElementSibling

    // Stopping the function if the input field has no value.
//    if((firstField.value.trim() === "") || (secondField.value.trim() === "")){
//        return false;
//    }

    // creating the div container.
    let div = document.createElement("div");
    div.setAttribute("class", "field");

    // Creating the input elements.
    let field = document.createElement("input");
    field.setAttribute("type", "text");
    field.setAttribute("name", "!_or;_NAT-ROUTE"+rowNum);
    field.setAttribute("value", "!");
    let field2 = document.createElement("input");
    field2.setAttribute("type", "text");
    field2.setAttribute("name", "nat-ip-"+rowNum);
    let field3 = document.createElement("input");
    field3.setAttribute("type", "text");
    field3.setAttribute("name", "nat-mask-"+rowNum);
    let field4 = document.createElement("input");
    field4.setAttribute("type", "text");
    field4.setAttribute("name", "nat-next-hop-"+rowNum);
    let field5 = document.createElement("input");
    field5.setAttribute("type", "text");
    field5.setAttribute("name", "tag-"+rowNum);

    // Creating the plus span element.
    let plus = document.createElement("plus");
    plus.setAttribute("onclick", "addField(this)");
    let plusText = document.createTextNode("+");
    plus.appendChild(plusText);

    // Creating the minus span element.
    let minus = document.createElement("minus");
    minus.setAttribute("onclick", "removeField(this)");
    let minusText = document.createTextNode("-");
    minus.appendChild(minusText);

    // Adding the elements to the DOM. Add div after lastField
    lastField.after(div)
    div.innerHTML = rowNum + ":";
    div.appendChild(field);
    div.appendChild(field2);
    div.appendChild(field3);
    div.appendChild(field4);
    div.appendChild(field5);
    div.appendChild(plus);
    div.appendChild(minus);

    // Un hiding the minus sign.
//    plusElement.nextElementSibling.style.display = "block"; // the minus sign
    plusElement.nextElementSibling.style.display = "none"; // the minus sign

    // Hiding the plus sign.
    plusElement.style.display = "none"; // the plus sign
    rowNum = rowNum + 1;
}

function removeField(minusElement){
//    minusElement.parentElement.previousElementSibling.remove();
    let previousMinus = minusElement.parentElement.previousElementSibling.lastElementChild;
    previousMinus.style.display = "block";
    previousMinus.previousElementSibling.style.display = "block";
    minusElement.parentElement.remove();
    rowNum = rowNum - 1;
}

let form = document.forms[0];




//      form.addEventListener("submit", fetchTextNotes);
//      function fetchTextNotes(event){
//          // prevent the form to communicate with the server.
//          event.preventDefault();
//
//          // Fetch the values from the input fields.
//          let data = new FormData(form);
//
//          // Storing the values inside an array so we can handle them.
//          // we don't want empty values.
//          let notes = [];
//          data.forEach( function(value){
//              if(value !== ""){
//                  notes.push(value);
//              }
//          });
//
//          // Output the values on the screen.
//          let out = "";
//          for(let note of notes){
//              out += `
//                  <p>${note} <span onclick="markAsDone(this)">Mark as done</span></p>
//              `;
//          }
//          document.querySelector(".notes").innerHTML = out;
//
//          // Delete all input elements except the last one.
//          let inputFields = document.querySelectorAll(".field");
//          inputFields.forEach(function(element, index){
//              if(index == inputFields.length - 1){
//                  element.children[0].value = "";
//              }else{
//                  element.remove();
//              }
//          });
//      }

//function markAsDone(element){
//    element.classList.add("mark");
//    element.innerHTML = "&check;";
//}