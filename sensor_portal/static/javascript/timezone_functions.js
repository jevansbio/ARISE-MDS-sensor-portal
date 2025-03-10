const timezonesWithoffsets = Intl.supportedValuesOf("timeZone").map(
  (timeZone) => {
    let offset = new Intl.DateTimeFormat("en-GB", {
      timeZone: timeZone,
      timeZoneName: "longOffset",
    })
      .formatToParts()
      .find((part) => part.type === "timeZoneName")
      .value.replace("GMT", "UTC");
    let abbreviation = new Intl.DateTimeFormat("en-GB", {
      timeZone: timeZone,
      timeZoneName: "short",
    })
      .formatToParts()
      .find((part) => part.type === "timeZoneName")
      .value.replace("GMT", "UTC");
    if (offset === "UTC") {
      offset = "UTC+00:00";
    }
    let sortOffset = Number(
      offset.replace("UTC", "").replace("+", "").replace(":", ".")
    );
    return {
      timeZone: timeZone,
      abbreviation: abbreviation,
      offset: offset,
      sortOffset: sortOffset,
    };
  }
);

const browserTimezone = new Intl.DateTimeFormat("en-GB", {
  timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  timeZoneName: "short",
})
  .formatToParts()
  .find((part) => part.type === "timeZoneName")
  .value.replace("GMT", "UTC");
let browserTimezoneOffset = new Intl.DateTimeFormat("en-GB", {
  timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  timeZoneName: "longOffset",
})
  .formatToParts()
  .find((part) => part.type === "timeZoneName")
  .value.replace("GMT", "UTC");
if (browserTimezoneOffset === "UTC") {
  browserTimezoneOffset = "UTC+00:00";
}

function loadTimeZoneList() {
  let allSelect = document.querySelectorAll(".dropdownTimeZone");

  allSelect.forEach((select) => {
    let newSelect = new TomSelect(select, {
      allowEmptyOption: false,
      hidePlaceholder: true,
      sortField: {
        field: "sortOffset",
        direction: "asc",
      },
    });
    for (const timeZone of timezonesWithoffsets) {
      newSelect.addOption({
        text: `${timeZone["abbreviation"]} ${timeZone["offset"]}`,
        value: timeZone["abbreviation"],
        sortOffset: timeZone["sortOffset"],
        offset: timeZone["offset"],
      });
    }
    newSelect.addOption({
      text: "GMT UTC+00:00",
      value: "UTC+00:00",
      offset: "UTC+00:00",
      sortOffset: 0,
    });
    newSelect.addItem(browserTimezone);
  });
}

function getTimeZoneCode(datetime) {
  return datetime
    .toLocaleDateString("en-GB", { day: "2-digit", timeZoneName: "short" })
    .substring(4);
}

function getOffset(timeZoneCode, removeUTC = false) {
  //console.log(timeZoneCode);
  let timeZone = timezonesWithoffsets.find(
    (element) => element["abbreviation"] === timeZoneCode
  );
  let offset = timeZone["offset"];
  if (removeUTC) {
    offset = offset.replace("UTC", "");
  }
  return offset;
}

const dtFormat = new Intl.DateTimeFormat("en-GB", {
  year: "numeric",
  month: "numeric",
  day: "numeric",
  hour: "numeric",
  minute: "numeric",
  second: "numeric",
  timeZoneName: "short",
});

// function tzStringFromTimeZoneCode(timeZoneCode){
//     let timeZone = timezonesWithoffsets.find((element) => element['abbreviation']==timeZoneCode)['timeZone']
//     return timeZone
// }

function nativeTZ(date) {
  let newdate = `${date.getFullYear()}-${padInt(date.getMonth() + 1)}-${padInt(
    date.getDate()
  )}T${padInt(date.getHours())}:${padInt(date.getMinutes())}:${padInt(
    date.getSeconds()
  )}.${date.getMilliseconds()}`;
  return newdate;
}

function padInt(n) {
  return String(n).padStart(2, "0");
}
