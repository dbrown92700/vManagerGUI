// This method will add a new row
function addNewRow(table){
//    console.log(table.id);
    var maxRows = document.getElementById(table.id+"-maxrows").innerText;
//    console.log(maxRows);
    var rowCount = table.rows.length;
//    console.log(rowCount);
    if (rowCount === Number(maxRows)+1) {
        alert("At maximum rows supported by this category.");
        return;
    }
    var cellCount = table.rows[0].cells.length;
    var row = table.insertRow(rowCount);
    for(var i =0; i < cellCount; i++){
        var cell = row.insertCell(i);
        var cellName = table.rows[0].cells[i].innerText;
        cell.innerHTML='<input type="text" name="'+cellName.replace("###", rowCount)+'"/>';
//        else{
//          cell.innerHTML = '<input type="button" value="delete" onclick="deleteRow(this)" />';
//          cell.innerHTML = '<input type="button" value="Add Row" onclick="addNewRow()" />';
//        }
    }
}
// This method will delete a row
function deleteRow(table){
    var rowCount = table.rows.length;
    if(rowCount <= 1){
        alert("There is no row available to delete!");
        return;
    }
    table.deleteRow(rowCount-1);
}

function addField(plusElement) {

    // If max rows are displayed don't do anything
    if (rowNum === (maxRowNum + 1)) {return false;}

    let lastField = document.getElementById("fieldTable").lastChild;

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