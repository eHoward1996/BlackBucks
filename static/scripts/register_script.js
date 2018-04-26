function addIP()    {
    var ip = document.getElementById("ip_addr").value;
    var div = document.getElementById("added");
    var txt = document.createElement("input");
    txt.appendChild(document.createTextNode(ip));
    txt.setAttribute("name", "node_addr");
    txt.setAttribute("value", ip);
    txt.setAttribute("readonly", "true");
    div.appendChild(txt);
    div.appendChild(document.createElement("br"));

    document.getElementById("sub").style.visibility = "visible"
}