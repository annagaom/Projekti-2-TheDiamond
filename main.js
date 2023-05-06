'use strict';
// show map using Leaflet library. (L comes from the Leaflet library)
const map = L.map('map', {tap: false});

L.tileLayer('https:{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
  maxZoom: 20,
  subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
}).addTo(map);
map.setView([60, 24], 7);

const apiurl = 'http://127.0.0.1:5002';
let playerRange;
const moves = [];
let userAnswer = document.querySelector('#answer').value;

// Create a marker bubble icon
const orangeIcon = L.icon({
        iconUrl: "img/oranssi.png",
        iconSize: [25, 40],
        iconAnchor: [12, 41],
        popupAnchor: [0, -35]
    });

const blueIcon = L.icon({
    iconUrl: "img/sininen.png",
    iconSize: [25, 40],
    iconAnchor: [12, 41],
    popupAnchor: [0, -35]
});

const startIcon = L.icon({
    iconUrl: "img/start.png",
    iconSize: [25, 40],
    iconAnchor: [12, 41],
    popupAnchor: [0, -35]
});


// function to fetch data from API
async function getData(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Inlavid server input');
  }
  const data = await response.json();
  return data
}


// game start when user insert player name
const playerForm = document.getElementById("player-form");
playerForm.addEventListener("submit", function(event) {
  event.preventDefault(); // prevent the default form submission behavior

  // Get the player name input value
  const playerNameInput = document.getElementById("player-input");
  const playerName = playerNameInput.value;
  document.querySelector('#player-modal').classList.add('hidden');
  gameSetup(`${apiurl}/newgame?player=${playerName}`);
});

const dialogX = document.querySelector('dialog span');
const dialog = document.querySelector('dialog');
const modalTitle = document.querySelector('#modal-title');
const modalText = document.querySelector('#modal-text');
const dialogImg = document.querySelector('dialog img');

dialogX.addEventListener('click', function(evt) {
  dialog.close();
})

// show math task when click
document.querySelector('#task-button').addEventListener('click', function() {
  document.querySelector('#task').style.textIndent = '0';
})

// function to update game info
function updateGame(game) {
  document.querySelector('#player-name').innerHTML = game.name;
  document.querySelector('#p-flight').innerHTML = game.flight;
  document.querySelector('#p-range').innerHTML = game.range;
  let currentToDiamond = document.querySelector('#goal-distance');
  if (game.distance_to_goal <= 300) {
    currentToDiamond.innerHTML = " 0 - 300 km.";
  } else if (game.distance_to_goal > 300 && game.distance_to_goal <= 500) {
    currentToDiamond.innerHTML = " 300 - 500 km.";
  } else if (game.distance_to_goal > 500 && game.distance_to_goal <= 800) {
    currentToDiamond.innerHTML = " 500 - 800 km.";
  } else if (game.distance_to_goal > 800 && game.distance_to_goal <= 1000) {
    currentToDiamond.innerHTML = " 800 - 1000 km.";
  } else if (game.distance_to_goal > 1000 && game.distance_to_goal <= 1500) {
    currentToDiamond.innerHTML = " 1000 - 1500 km.";
  } else if (game.distance_to_goal > 1500 && game.distance_to_goal <= 2000) {
    currentToDiamond.innerHTML = " 1500 - 2000 km.";
  } else if (game.distance_to_goal > 2000 && game.distance_to_goal <= 2500) {
    currentToDiamond.innerHTML = " 2000 - 2500 km.";
  } else if (game.distance_to_goal > 2500) {
    currentToDiamond.innerHTML = " yli 2500 km.";
  } else {
    currentToDiamond.innerHTML = "abc";
  }
}

// function to show game task
function updateTask(task) {
  document.querySelector('#task').style.textIndent = '-99em';
  document.querySelector('#task').value = task.name;

  document.querySelector('#answer').value = '';
  if (document.querySelector('#task-notification')) {
    document.querySelector('#task-notification').textContent = '';
  }
}

const taskSubmitButton = document.querySelector('#task-submit-button');
const p = document.createElement('p');
p.id = 'task-notification';
// calc range value after submitted answer
function calcRange(task, range) {
  const answer = document.querySelector('#answer').value;
  const parentTr = taskSubmitButton.parentNode;
  const button = taskSubmitButton;
  //console.log(`task.answer ${task.answer}, user answer: ${answer}, range: ${range}`);
  if (parseInt(answer) === task.answer) {
    p.textContent = "Oikein! Saat 500 km:ä!";
    range += 500;
    parentTr.insertBefore(p, button);
  } else if (parseInt(answer) !== task.answer) {
    p.textContent = "Väärin! Menetät 50 km:ä";
    parentTr.insertBefore(p, button);
    range -= 50;
  } else {
    p.textContent = "ABS!";
    parentTr.insertBefore(p, button);
  }
  //console.log(range);
  return range
}


// function to check if game over
function checkGameOver(flight, rangeToFly) {
  if (flight === 0) {
    console.log('Lennot on loppunut!');
    modalTitle.innerHTML = 'Game over!';
    dialogImg.src = 'img/game_over.gif';
    modalText.innerHTML = `Lennot ovat loppuneet. <br>
        Ikävä, et löysi timantin tällä kerralla. Kokeilla uudestaan!`
    return true
  } else if (rangeToFly === false) {
    console.log('Ei riittäviä kilometrejä lentämiseen');
    modalTitle.innerHTML = 'Game over!';
    dialogImg.src = 'img/game_over.gif';
    modalText.innerHTML = `Sinulla ei ole riittävää kilometriä lentämiseen. <br>
        Ikävä, et löysi timantin tällä kerralla. Kokeilla uudestaan!`;
    return true
  }
  return false
}

// check if player went to the airport that has diamond, current & diamond on airport code
function checkGameWin(current, diamond) {
  if (current === diamond) {
    console.log(current, diamond);
    console.log('You won.');
    modalTitle.innerHTML = 'Onnea! Voitit pelin!';
    modalText.innerHTML = '';
    dialogImg.src = 'img/win.jpg';
    return true;
  }
  return false;
}




// function for game start
async function gameSetup(url) {

  try {
    const gameData = await getData(url);
    console.log(gameData);
    updateGame(gameData.game);
    updateTask(gameData.task);
    let gameWin = checkGameWin(gameData.game.player_loc.ident,gameData.game.diamond.location);
    let gameOver = checkGameOver(gameData.game.flight, gameData.game.range_to_flight);
    playerRange = gameData.game.range;
    taskSubmitButton.addEventListener('click', function updateRange(evt) {
      playerRange = calcRange(gameData.task, gameData.game.range);
      console.log(playerRange);
      document.querySelector('#p-range').innerHTML = playerRange;
      taskSubmitButton.disabled = true;

    })

    for (let airport of gameData.airports) {
      const marker = L.marker([airport.latitude_deg, airport.longitude_deg]).addTo(map);
        if (airport.active) {
          map.flyTo([airport.latitude_deg, airport.longitude_deg], 7);
          marker.bindPopup(`Olet tässä ${airport.name}, ${airport.country_name} `)
          moves.push(airport);
          marker.openPopup()
          marker.setIcon(startIcon);

        } else {
          if (moves.includes(airport)) {
            marker.setIcon(startIcon);
          } else {
            marker.setIcon(blueIcon);
          }

          //marker.bindPopup(`${airport.name}. <br>Etäisyys sijainista noin ${airport.distance} km`);

          const popupContent = document.createElement('div');
          const h4 = document.createElement('h4');
          h4.innerHTML = `${airport.name} - lentolenttä`;
          popupContent.append(h4);


          try {
            const apikey = 'b4ff2fa580bc05168e686ad6b45cb1c6';
            const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${airport.latitude_deg}&lon=${airport.longitude_deg}&appid=${apikey}`)
            if (!response.ok) {
              throw new Error('Invalid server input');
            }
            const data = await response.json();
            const c = (data['main']['temp']) - 273.15;
            const weather = data.weather[0].description;
            const temperature = `${c.toFixed(1)}°C`;
            const icon = data.weather[0].icon;
            const iconUrl = `https://openweathermap.org/img/w/${icon}.png`;


            console.log(data);
            const p = document.createElement('p');
            p.innerHTML = `Temperature: ${temperature}<br> Weather: ${weather}`;
            popupContent.append(p);
            marker.bindPopup(popupContent);

            const img = document.createElement('img');
            img.src = iconUrl;
            popupContent.appendChild(img);

          } catch (error) {
            console.log(error);
          }

          const goButton = document.createElement('button');
          goButton.classList.add('button');
          goButton.innerHTML = 'Lennä tänne';
          popupContent.append(goButton);
          const p = document.createElement('p');
          p.innerHTML = `Etäisyys ${airport.distance} km`;
          popupContent.append(p);
          marker.bindPopup(popupContent);

          goButton.addEventListener('click', function (evt) {
            evt.stopPropagation();
            evt.preventDefault();
            if (playerRange < airport.distance) {
              console.log(playerRange);
              marker.bindPopup(`Sinulla ei ole riittävästi kilometrejä lentääksesi tänne!`);
            } else if (gameData.game.flight === 0) {
              marker.bindPopup(`Sinulla ei ole riittävää lentoa.`);
            } else if (gameWin) {
              marker.bindPopup(`Voitit jo tällä kertaa.`);
            } else {
              // player's new range and flight
              playerRange = playerRange - airport.distance;
              let playerFlight = gameData.game.flight - 1;
              taskSubmitButton.disabled = false;
              //document.querySelector('#invisible').classList.add('invisible');
              // call flyto api http://127.0.0.1:5000/flyto?game=30&dest=EFPO&range=700&flight=14
              gameSetup(`${apiurl}/flyto?game=${gameData.game.id}
              &dest=${airport.ident}&range=${playerRange}&flight=${playerFlight}`);
            }
          });
        }
    }
    if (gameWin) {
      taskSubmitButton.disabled = true;
      dialog.showModal();
      return
    }
    if (gameOver) {
      taskSubmitButton.disabled = true;
      console.log('Game over');
      modalText.innerHTML += `<br>Timantti sijaitsi ${gameData.game.diamond.airport_name}. `;
      dialog.showModal();
      return
    }


  } catch (error) {
    console.log(error);
  }
}


// gameSetup('http://127.0.0.1:5000/newgame?player=Martti');





